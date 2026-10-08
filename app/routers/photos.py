"""Vehicle photo endpoints backed by Backblaze B2."""

from __future__ import annotations

from io import BytesIO
from uuid import uuid4

import psycopg
from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Response, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.config import get_settings
from app.database import get_connection
from app.schemas.photo import VehiclePhotoResponse
from app.storage import StorageError, create_download_url, delete_image, upload_image


router = APIRouter(prefix="/veiculos/{veiculo_id}/fotos", tags=["vehicle photos"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PHOTOS_PER_VEHICLE = 5
MAX_IMAGE_DIMENSION = 2400
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def prepare_image(upload: UploadFile) -> bytes:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato permitido: JPEG, PNG ou WebP",
        )

    raw_content = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if not raw_content:
        raise HTTPException(status_code=422, detail="Arquivo de imagem vazio")
    if len(raw_content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="A imagem deve ter no maximo 5 MB",
        )

    try:
        with Image.open(BytesIO(raw_content)) as source:
            source.load()
            image = ImageOps.exif_transpose(source)
            image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")

            output = BytesIO()
            image.save(output, format="WEBP", quality=85, method=6)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise HTTPException(status_code=422, detail="Arquivo de imagem invalido") from error


def serialize_photo(row: dict) -> dict:
    return {
        "foto_id": row["foto_id"],
        "veiculo_id": row["veiculo_id"],
        "foto_url": create_download_url(row["object_key"]),
        "thumb": row["thumb"],
    }


@router.post("", response_model=VehiclePhotoResponse, status_code=status.HTTP_201_CREATED)
def upload_vehicle_photo(
    file: UploadFile = File(...),
    thumb: bool = Form(False),
    veiculo_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    image_content = prepare_image(file)
    settings = get_settings()
    object_key = f"{settings.b2_object_prefix}/{uuid4()}.webp"
    uploaded = False

    try:
        with get_connection() as connection:
            vehicle = connection.execute(
                """
                SELECT veiculo_id
                FROM veiculos
                WHERE veiculo_id = %(veiculo_id)s
                  AND empresa_id = %(empresa_id)s
                FOR UPDATE
                """,
                {
                    "veiculo_id": veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not vehicle:
                raise HTTPException(status_code=404, detail="Veiculo nao encontrado")

            photo_count = connection.execute(
                "SELECT COUNT(*) FROM fotos WHERE veiculo_id = %(veiculo_id)s",
                {"veiculo_id": veiculo_id},
            ).fetchone()["count"]
            if photo_count >= MAX_PHOTOS_PER_VEHICLE:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="O veiculo ja possui o limite de 5 fotos",
                )

            upload_image(object_key, image_content)
            uploaded = True

            should_be_thumb = thumb or photo_count == 0
            if should_be_thumb:
                connection.execute(
                    "UPDATE fotos SET thumb = FALSE WHERE veiculo_id = %(veiculo_id)s",
                    {"veiculo_id": veiculo_id},
                )

            photo = connection.execute(
                """
                INSERT INTO fotos (veiculo_id, object_key, thumb)
                VALUES (%(veiculo_id)s, %(object_key)s, %(thumb)s)
                RETURNING foto_id, veiculo_id, object_key, thumb
                """,
                {
                    "veiculo_id": veiculo_id,
                    "object_key": object_key,
                    "thumb": should_be_thumb,
                },
            ).fetchone()
    except HTTPException:
        raise
    except StorageError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except psycopg.Error as error:
        if uploaded:
            try:
                delete_image(object_key)
            except StorageError:
                pass
        raise HTTPException(status_code=503, detail="Nao foi possivel salvar a foto") from error

    return serialize_photo(photo)


@router.get("", response_model=list[VehiclePhotoResponse])
def list_vehicle_photos(
    veiculo_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[dict]:
    try:
        with get_connection() as connection:
            vehicle = connection.execute(
                """
                SELECT 1 FROM veiculos
                WHERE veiculo_id = %(veiculo_id)s
                  AND empresa_id = %(empresa_id)s
                """,
                {
                    "veiculo_id": veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not vehicle:
                raise HTTPException(status_code=404, detail="Veiculo nao encontrado")

            photos = connection.execute(
                """
                SELECT foto_id, veiculo_id, object_key, thumb
                FROM fotos
                WHERE veiculo_id = %(veiculo_id)s
                ORDER BY thumb DESC, foto_id
                """,
                {"veiculo_id": veiculo_id},
            ).fetchall()
    except HTTPException:
        raise
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel listar as fotos") from error

    try:
        return [serialize_photo(photo) for photo in photos]
    except StorageError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.patch("/{foto_id}/thumb", response_model=VehiclePhotoResponse)
def set_vehicle_thumbnail(
    veiculo_id: int = Path(gt=0),
    foto_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            photo = connection.execute(
                """
                SELECT foto.foto_id, foto.veiculo_id, foto.object_key, foto.thumb
                FROM fotos AS foto
                INNER JOIN veiculos AS veiculo
                    ON veiculo.veiculo_id = foto.veiculo_id
                WHERE foto.foto_id = %(foto_id)s
                  AND foto.veiculo_id = %(veiculo_id)s
                  AND veiculo.empresa_id = %(empresa_id)s
                FOR UPDATE OF foto
                """,
                {
                    "foto_id": foto_id,
                    "veiculo_id": veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not photo:
                raise HTTPException(status_code=404, detail="Foto nao encontrada")

            connection.execute(
                "UPDATE fotos SET thumb = FALSE WHERE veiculo_id = %(veiculo_id)s",
                {"veiculo_id": veiculo_id},
            )
            photo = connection.execute(
                """
                UPDATE fotos SET thumb = TRUE
                WHERE foto_id = %(foto_id)s
                RETURNING foto_id, veiculo_id, object_key, thumb
                """,
                {"foto_id": foto_id},
            ).fetchone()
    except HTTPException:
        raise
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel definir a thumbnail") from error

    try:
        return serialize_photo(photo)
    except StorageError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.delete(
    "/{foto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_vehicle_photo(
    veiculo_id: int = Path(gt=0),
    foto_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> Response:
    try:
        with get_connection() as connection:
            photo = connection.execute(
                """
                SELECT foto.foto_id, foto.object_key, foto.thumb
                FROM fotos AS foto
                INNER JOIN veiculos AS veiculo
                    ON veiculo.veiculo_id = foto.veiculo_id
                WHERE foto.foto_id = %(foto_id)s
                  AND foto.veiculo_id = %(veiculo_id)s
                  AND veiculo.empresa_id = %(empresa_id)s
                FOR UPDATE OF foto
                """,
                {
                    "foto_id": foto_id,
                    "veiculo_id": veiculo_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not photo:
                raise HTTPException(status_code=404, detail="Foto nao encontrada")

            delete_image(photo["object_key"])
            connection.execute(
                "DELETE FROM fotos WHERE foto_id = %(foto_id)s",
                {"foto_id": foto_id},
            )

            if photo["thumb"]:
                replacement = connection.execute(
                    """
                    SELECT foto_id FROM fotos
                    WHERE veiculo_id = %(veiculo_id)s
                    ORDER BY foto_id
                    LIMIT 1
                    """,
                    {"veiculo_id": veiculo_id},
                ).fetchone()
                if replacement:
                    connection.execute(
                        "UPDATE fotos SET thumb = TRUE WHERE foto_id = %(foto_id)s",
                        {"foto_id": replacement["foto_id"]},
                    )
    except HTTPException:
        raise
    except StorageError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel excluir a foto") from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
