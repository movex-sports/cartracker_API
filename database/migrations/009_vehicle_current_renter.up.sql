-- Interrompe a migration com seguranca se ja houver mais de um locatario por veiculo.
CREATE UNIQUE INDEX locatarios_veiculo_unique_guard_idx
    ON locatarios (veiculo_id);

ALTER TABLE veiculos
    ADD COLUMN locatario_id BIGINT;

UPDATE veiculos AS veiculo
SET locatario_id = locatario.locatario_id
FROM locatarios AS locatario
WHERE locatario.veiculo_id = veiculo.veiculo_id
  AND locatario.empresa_id = veiculo.empresa_id;

ALTER TABLE locatarios
    ADD CONSTRAINT locatarios_id_empresa_unique
        UNIQUE (locatario_id, empresa_id);

ALTER TABLE veiculos
    ADD CONSTRAINT veiculos_locatario_empresa_fk
        FOREIGN KEY (locatario_id, empresa_id)
        REFERENCES locatarios (locatario_id, empresa_id)
        ON UPDATE CASCADE ON DELETE RESTRICT;

CREATE UNIQUE INDEX veiculos_locatario_id_unique_idx
    ON veiculos (locatario_id)
    WHERE locatario_id IS NOT NULL;

DROP INDEX locatarios_veiculo_unique_guard_idx;
DROP INDEX locatarios_veiculo_id_idx;

ALTER TABLE locatarios
    DROP CONSTRAINT locatarios_veiculo_empresa_fk,
    DROP COLUMN veiculo_id;
