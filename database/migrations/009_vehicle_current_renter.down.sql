ALTER TABLE locatarios
    ADD COLUMN veiculo_id BIGINT;

UPDATE locatarios AS locatario
SET veiculo_id = veiculo.veiculo_id
FROM veiculos AS veiculo
WHERE veiculo.locatario_id = locatario.locatario_id
  AND veiculo.empresa_id = locatario.empresa_id;

ALTER TABLE locatarios
    ALTER COLUMN veiculo_id SET NOT NULL,
    ADD CONSTRAINT locatarios_veiculo_empresa_fk
        FOREIGN KEY (veiculo_id, empresa_id)
        REFERENCES veiculos (veiculo_id, empresa_id)
        ON UPDATE CASCADE ON DELETE RESTRICT;

CREATE INDEX locatarios_veiculo_id_idx ON locatarios (veiculo_id);

DROP INDEX veiculos_locatario_id_unique_idx;

ALTER TABLE veiculos
    DROP CONSTRAINT veiculos_locatario_empresa_fk,
    DROP COLUMN locatario_id;

ALTER TABLE locatarios
    DROP CONSTRAINT locatarios_id_empresa_unique;
