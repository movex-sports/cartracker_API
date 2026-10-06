ALTER TABLE veiculos
    ADD COLUMN owner_id BIGINT;

UPDATE veiculos AS veiculo
SET owner_id = empresa.user_id
FROM empresas AS empresa
WHERE empresa.empresa_id = veiculo.empresa_id;

DROP INDEX veiculos_empresa_id_idx;

ALTER TABLE veiculos
    ALTER COLUMN owner_id SET NOT NULL,
    ADD CONSTRAINT veiculos_owner_fk
        FOREIGN KEY (owner_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    DROP CONSTRAINT veiculos_empresa_fk,
    DROP COLUMN empresa_id;

CREATE INDEX veiculos_owner_id_idx ON veiculos (owner_id);

DROP INDEX users_empresa_id_idx;

ALTER TABLE users
    ADD COLUMN is_owner BOOLEAN NOT NULL DEFAULT FALSE,
    DROP CONSTRAINT users_empresa_fk,
    DROP COLUMN empresa_id;

DROP TABLE empresas;
