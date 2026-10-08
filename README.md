# Car Tracker API

API HTTP do Car Tracker, criada com FastAPI e PostgreSQL.

## Desenvolvimento local

Crie `.env` a partir de `.env.example` e instale as dependencias:

```powershell
python -m pip install -r requirements.txt
python database/migrate.py up
python -m uvicorn app.main:app --reload
```

A API fica disponivel em `http://127.0.0.1:8000` e a documentacao interativa
em `http://127.0.0.1:8000/docs`.

## Render

Configure `DATABASE_URL` nas variaveis de ambiente do Web Service. Quando o
banco e a API estiverem na mesma regiao do Render, prefira a Internal Database
URL.

Configure tambem `ENVIRONMENT=production` e uma `JWT_SECRET` aleatoria com pelo
menos 32 caracteres. Nunca salve essa chave no repositorio.

Build Command:

```text
pip install -r requirements.txt
```

Start Command:

```text
python database/migrate.py up && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

O executor registra migrations em `schema_migrations`; por isso, reiniciar ou
refazer o deploy nao tenta recriar tabelas que ja existem.

## Endpoints iniciais

- `GET /`: identificacao e versao da API.
- `GET /health`: verifica a API e a conexao com PostgreSQL.
- `POST /users`: cadastra um usuario e armazena somente o hash bcrypt da senha.
- `POST /users/dependentes`: cadastra um usuario role 2 na empresa autenticada.
- `GET /users/dependentes`: lista usuarios role 2 da empresa autenticada.
- `DELETE /users/dependentes/{user_id}`: exclui um usuario role 2 da empresa.
- `POST /auth/login`: autentica por username ou e-mail e retorna um access token.
- `POST /auth/renew`: renova por mais 10 minutos um access token ainda valido.
- `POST /veiculos`: cadastra um veiculo para a empresa do usuario autenticado.
- `GET /veiculos`: lista os veiculos da empresa do usuario autenticado.
- `POST /hardware`: gera um hardware para a empresa informada e autenticada.
- `GET /catalogo/marcas`: lista marcas para o dropdown do frontend.
- `GET /catalogo/marcas/{marca_id}/modelos`: lista modelos de uma marca.
- `POST /veiculos/{veiculo_id}/locatarios`: cadastra um locatario no veiculo.
- `GET /locatarios`: lista locatarios da empresa, com filtro opcional por veiculo.
- `PATCH /locatarios/{locatario_id}/desativar`: desativa e libera o veiculo.
- `PATCH /locatarios/{locatario_id}/ativar`: reativa e atribui um veiculo livre.
- `POST /veiculos/{veiculo_id}/fotos`: envia uma foto em multipart para o B2.
- `GET /veiculos/{veiculo_id}/fotos`: lista fotos com URLs temporarias.
- `PATCH /veiculos/{veiculo_id}/fotos/{foto_id}/thumb`: define a foto principal.
- `DELETE /veiculos/{veiculo_id}/fotos/{foto_id}`: exclui a foto.

Os arquivos sao armazenados no B2 como `fotos_veiculares/{uuid}.webp`. O
relacionamento com empresa e veiculo permanece no banco de dados.
`GET /veiculos` inclui `foto_thumb_url`, com URL temporaria da foto principal,
ou `null` quando o veiculo ainda nao possui thumbnail.
As CNHs dos locatarios ficam em `documentos_locatarios/{uuid}.pdf` e podem ser
enviadas, consultadas ou excluidas em `/locatarios/{locatario_id}/documentos/cnh`.
O upload aceita exclusivamente PDF de ate 10 MB.
Na exclusao, a API remove permanentemente todas as versoes e marcadores do
objeto no B2; a Application Key precisa da permissao `deleteFiles`.
- `GET /docs`: documentacao OpenAPI interativa.

O frontend deve chamar `/auth/renew` em cada nova navegacao, antes de o token
atual expirar, enviando-o no cabecalho:

```text
Authorization: Bearer ACCESS_TOKEN_ATUAL
```

A resposta contem um novo `access_token` valido por 10 minutos. Se o token
anterior ja estiver expirado, a API responde `401` e um novo login e necessario.

No cadastro, `role` e definido internamente como `"1"` e `status` como `true`.
A mesma transacao cria uma empresa ativa, ainda sem nome, e devolve seu
`empresa_id`. Esses campos nao fazem parte do payload.
