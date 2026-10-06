# Banco de dados do Car Tracker

Estrutura inicial para PostgreSQL, baseada no modelo fornecido.

## Tabelas e relacionamentos

- `users`: cadastro, endereco, acesso e situacao dos usuarios.
- `veiculos`: dados dos veiculos. `owner_id` referencia `users.user_id`.
- `fotos`: imagens dos veiculos. `veiculo_id` referencia `veiculos.veiculo_id`.

Um usuario pode possuir varios veiculos, e um veiculo pode possuir varias fotos.
Ao excluir um veiculo, suas fotos sao excluidas em cascata. Um usuario que ainda
possui veiculos nao pode ser excluido.

## Convencoes adotadas

- CPF e CEP sao armazenados somente com numeros.
- Estado usa a sigla em letras maiusculas, por exemplo `SP`.
- Placa usa sete caracteres alfanumericos, sem hifen e em letras maiusculas.
- Senhas devem ser processadas pela API com Argon2id ou bcrypt; o banco recebe
  somente o hash em `password_hash`.
- Valores de capacidade, consumo, velocidade e odometro usam tipos decimais.
- Cada veiculo pode ter no maximo uma foto com `thumb = true`.
- E-mail, CPF, username e placa possuem regras de unicidade.

## Executar a migration

Com a variavel `DATABASE_URL` configurada para uma instancia PostgreSQL:

```powershell
psql $env:DATABASE_URL -f database/migrations/001_initial_schema.up.sql
```

Para reverter completamente essa migration:

```powershell
psql $env:DATABASE_URL -f database/migrations/001_initial_schema.down.sql
```
