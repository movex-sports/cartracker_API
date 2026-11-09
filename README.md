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
- `POST /hardware`: cadastra um hardware, opcionalmente com o IMEI do rastreador.
- `PATCH /veiculos/{veiculo_id}/hardware`: vincula ou desvincula um hardware.
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

## Telemetria do hardware

- `POST /dados-crus`: recebe IMEI e telemetria usando o header
  `X-Hardware-Key`; a API resolve e grava `hardware_id` e `veiculo_id` em uma
  unica operacao no banco.
- `GET /dados-crus/veiculos-alugados`: lista os veiculos alugados da empresa
  autenticada e a leitura mais recente de cada um.

Configure `HARDWARE_INGEST_KEY` no Render com uma chave longa e aleatoria. Veiculos
sem nenhuma leitura aparecem no GET com os campos de telemetria iguais a `null`.
Como o hardware ja esta disponivel, configure a mesma `HARDWARE_INGEST_KEY` no
Render e no servico que publicara as leituras do rastreador.
O payload inicial do ESP32 contem `imei`, `data_hora` com fuso UTC, `velocidade`,
`latitude` e `longitude`. A API salva esse horario como `capturado_em` e tambem
preenche `registrado_em` com o momento em que recebeu a requisicao.
O banco guarda latitude e longitude em graus decimais; o GET tambem devolve
`coordenadas` no formato DMS, por exemplo `23°31'47.0\"S 46°50'41.5\"W`.
O GET de veiculos alugados tambem inclui `foto_thumb_url`, com uma URL assinada
temporaria da foto principal, ou `null` quando o veiculo nao possui thumbnail.
O mesmo retorno inclui nome, sobrenome e CPF do locatario atualmente vinculado
ao veiculo, evitando uma segunda consulta do frontend.

## Receptor G900L/J16

O diretorio `gt06_server` contem o receptor TCP diagnostico do protocolo GT06.
Ele escuta a porta configurada em `GT06_PORT` (5023 por padrao), valida CRC,
registra os pacotes recebidos e responde aos pacotes de login e heartbeat.
Consulte `gt06_server/README.md` para executar e testar. A publicacao automatica
na API sera habilitada depois de confirmar os campos enviados pelo firmware do
aparelho real.
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
