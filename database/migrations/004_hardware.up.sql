CREATE TABLE hardware (
    hardware_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    empresa_id BIGINT NOT NULL,

    CONSTRAINT hardware_empresa_fk
        FOREIGN KEY (empresa_id) REFERENCES empresas (empresa_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT hardware_id_empresa_unique UNIQUE (hardware_id, empresa_id)
);

CREATE INDEX hardware_empresa_id_idx ON hardware (empresa_id);

ALTER TABLE veiculos
    ADD COLUMN hardware_id BIGINT,
    ADD CONSTRAINT veiculos_hardware_empresa_fk
        FOREIGN KEY (hardware_id, empresa_id)
        REFERENCES hardware (hardware_id, empresa_id)
        ON UPDATE CASCADE ON DELETE RESTRICT;

CREATE UNIQUE INDEX veiculos_hardware_id_unique_idx
    ON veiculos (hardware_id)
    WHERE hardware_id IS NOT NULL;
