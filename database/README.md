# Banco de dados do Car Tracker

Estrutura inicial para PostgreSQL, baseada no modelo fornecido.

## Tabelas e relacionamentos

- `users`: cadastro, endereco, acesso e situacao dos usuarios. `empresa_id`
  identifica a empresa a que o usuario pertence.
- `empresas`: empresas e frotas. `user_id` identifica o usuario fundador.
- `veiculos`: dados dos veiculos. `empresa_id` referencia `empresas.empresa_id`.
- `fotos`: imagens dos veiculos. `veiculo_id` referencia `veiculos.veiculo_id`.

Uma empresa pode possuir varios usuarios e veiculos, e um veiculo pode possuir
varias fotos. Ao excluir um veiculo, suas fotos sao excluidas em cascata.

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

Com a variavel `DATABASE_URL` configurada no arquivo `.env` e o pacote
`psycopg` instalado:

```powershell
python database/migrate.py up
```

Para reverter completamente essa migration:

```powershell
python database/migrate.py down
```
