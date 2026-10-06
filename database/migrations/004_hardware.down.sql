DROP INDEX veiculos_hardware_id_unique_idx;

ALTER TABLE veiculos
    DROP CONSTRAINT veiculos_hardware_empresa_fk,
    DROP COLUMN hardware_id;

DROP INDEX hardware_empresa_id_idx;
DROP TABLE hardware;
