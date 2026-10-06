CREATE TABLE empresas (
    empresa_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150),
    status BOOLEAN NOT NULL DEFAULT TRUE,
    user_id BIGINT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT empresas_user_fk
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT empresas_nome_not_blank_check
        CHECK (nome IS NULL OR BTRIM(nome) <> '')
);

-- Preserva usuarios que possam ter sido cadastrados antes desta migration.
INSERT INTO empresas (user_id)
SELECT user_id
FROM users;

ALTER TABLE users
    ADD COLUMN empresa_id BIGINT;

UPDATE users AS usuario
SET empresa_id = empresa.empresa_id
FROM empresas AS empresa
WHERE empresa.user_id = usuario.user_id;

ALTER TABLE users
    ALTER COLUMN empresa_id SET NOT NULL,
    ADD CONSTRAINT users_empresa_fk
        FOREIGN KEY (empresa_id) REFERENCES empresas (empresa_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    DROP COLUMN is_owner;

CREATE INDEX users_empresa_id_idx ON users (empresa_id);

ALTER TABLE veiculos
    ADD COLUMN empresa_id BIGINT;

UPDATE veiculos AS veiculo
SET empresa_id = usuario.empresa_id
FROM users AS usuario
WHERE usuario.user_id = veiculo.owner_id;

DROP INDEX veiculos_owner_id_idx;

ALTER TABLE veiculos
    ALTER COLUMN empresa_id SET NOT NULL,
    ADD CONSTRAINT veiculos_empresa_fk
        FOREIGN KEY (empresa_id) REFERENCES empresas (empresa_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    DROP CONSTRAINT veiculos_owner_fk,
    DROP COLUMN owner_id;

CREATE INDEX veiculos_empresa_id_idx ON veiculos (empresa_id);
