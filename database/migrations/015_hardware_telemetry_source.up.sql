-- Os registros existentes foram criados apenas para validar manualmente o mapa.
DELETE FROM dados_crus;

ALTER TABLE hardware
    ADD COLUMN status BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE dados_crus
    ADD COLUMN hardware_id BIGINT NOT NULL,
    ADD CONSTRAINT dados_crus_hardware_fk
        FOREIGN KEY (hardware_id) REFERENCES hardware (hardware_id)
        ON UPDATE CASCADE ON DELETE RESTRICT;

CREATE INDEX dados_crus_hardware_latest_idx
    ON dados_crus (hardware_id, registrado_em DESC, status_id DESC);
