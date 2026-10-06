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
- `GET /docs`: documentacao OpenAPI interativa.

No cadastro, `role` e definido internamente como `"1"`, `is_owner` como `false`
e `status` como `true`; esses campos nao fazem parte do payload.
