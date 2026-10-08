"""Renter CNH endpoints backed by Backblaze B2."""

from __future__ import annotations

from pathlib import Path as FilePath
from uuid import uuid4

import psycopg
from fastapi import APIRouter, Depends, File, HTTPException, Path, Response, UploadFile, status

from app.auth_dependencies import AuthenticatedUser, require_authenticated_user
from app.config import get_settings
from app.database import get_connection
from app.schemas.renter_document import RenterDocumentResponse
from app.storage import (
    StorageError,
    create_download_url,
    delete_object,
    upload_object,
)


router = APIRouter(
    prefix="/locatarios/{locatario_id}/documentos/cnh",
    tags=["renter documents"],
)

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
PDF_CONTENT_TYPE = "application/pdf"


def read_document(upload: UploadFile) -> tuple[bytes, str]:
    if upload.content_type != PDF_CONTENT_TYPE:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="A CNH deve ser enviada em formato PDF",
        )

    content = upload.file.read(MAX_DOCUMENT_BYTES + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Arquivo da CNH vazio")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="O arquivo da CNH deve ter no maximo 10 MB",
        )
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="Arquivo PDF invalido")

    return content, ".pdf"


def serialize_document(row: dict) -> dict:
    return {
        "documento_id": row["documento_id"],
        "locatario_id": row["locatario_id"],
        "tipo": row["tipo"],
        "nome_original": row["nome_original"],
        "content_type": row["content_type"],
        "documento_url": create_download_url(row["object_key"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.post("", response_model=RenterDocumentResponse)
def upload_renter_cnh(
    file: UploadFile = File(...),
    locatario_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    content, extension = read_document(file)
    settings = get_settings()
    object_key = f"{settings.b2_renter_document_prefix}/{uuid4()}{extension}"
    original_name = FilePath(file.filename or f"cnh{extension}").name[:255]
    uploaded = False
    previous_object_key: str | None = None

    try:
        with get_connection() as connection:
            renter = connection.execute(
                """
                SELECT locatario_id
                FROM locatarios
                WHERE locatario_id = %(locatario_id)s
                  AND empresa_id = %(empresa_id)s
                FOR UPDATE
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not renter:
                raise HTTPException(status_code=404, detail="Locatario nao encontrado")

            previous = connection.execute(
                """
                SELECT object_key
                FROM documentos_locatarios
                WHERE locatario_id = %(locatario_id)s AND tipo = 'cnh'
                FOR UPDATE
                """,
                {"locatario_id": locatario_id},
            ).fetchone()
            previous_object_key = previous["object_key"] if previous else None

            upload_object(object_key, content, file.content_type or "", "documento")
            uploaded = True

            document = connection.execute(
                """
                INSERT INTO documentos_locatarios (
                    locatario_id, tipo, object_key, nome_original, content_type
                )
                VALUES (
                    %(locatario_id)s, 'cnh', %(object_key)s,
                    %(nome_original)s, %(content_type)s
                )
                ON CONFLICT (locatario_id, tipo) DO UPDATE SET
                    object_key = EXCLUDED.object_key,
                    nome_original = EXCLUDED.nome_original,
                    content_type = EXCLUDED.content_type,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING
                    documento_id, locatario_id, tipo, object_key,
                    nome_original, content_type, created_at, updated_at
                """,
                {
                    "locatario_id": locatario_id,
                    "object_key": object_key,
                    "nome_original": original_name,
                    "content_type": file.content_type,
                },
            ).fetchone()
    except HTTPException:
        raise
    except StorageError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except psycopg.Error as error:
        if uploaded:
            try:
                delete_object(object_key, "documento")
            except StorageError:
                pass
        raise HTTPException(status_code=503, detail="Nao foi possivel salvar a CNH") from error

    if previous_object_key and previous_object_key != object_key:
        try:
            delete_object(previous_object_key, "documento")
        except StorageError:
            pass

    try:
        return serialize_document(document)
    except StorageError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.get("", response_model=RenterDocumentResponse)
def get_renter_cnh(
    locatario_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict:
    try:
        with get_connection() as connection:
            document = connection.execute(
                """
                SELECT
                    documento.documento_id, documento.locatario_id,
                    documento.tipo, documento.object_key,
                    documento.nome_original, documento.content_type,
                    documento.created_at, documento.updated_at
                FROM documentos_locatarios AS documento
                INNER JOIN locatarios AS locatario
                    ON locatario.locatario_id = documento.locatario_id
                WHERE documento.locatario_id = %(locatario_id)s
                  AND documento.tipo = 'cnh'
                  AND locatario.empresa_id = %(empresa_id)s
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel consultar a CNH") from error

    if not document:
        raise HTTPException(status_code=404, detail="CNH nao encontrada")
    try:
        return serialize_document(document)
    except StorageError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_renter_cnh(
    locatario_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> Response:
    try:
        with get_connection() as connection:
            document = connection.execute(
                """
                SELECT documento.documento_id, documento.object_key
                FROM documentos_locatarios AS documento
                INNER JOIN locatarios AS locatario
                    ON locatario.locatario_id = documento.locatario_id
                WHERE documento.locatario_id = %(locatario_id)s
                  AND documento.tipo = 'cnh'
                  AND locatario.empresa_id = %(empresa_id)s
                FOR UPDATE OF documento
                """,
                {
                    "locatario_id": locatario_id,
                    "empresa_id": current_user.empresa_id,
                },
            ).fetchone()
            if not document:
                raise HTTPException(status_code=404, detail="CNH nao encontrada")

            delete_object(document["object_key"], "documento")
            connection.execute(
                "DELETE FROM documentos_locatarios WHERE documento_id = %(documento_id)s",
                {"documento_id": document["documento_id"]},
            )
    except HTTPException:
        raise
    except StorageError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel excluir a CNH") from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
