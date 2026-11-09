ALTER TABLE dados_crus
    ADD COLUMN capturado_em TIMESTAMPTZ;

UPDATE dados_crus
SET capturado_em = registrado_em
WHERE capturado_em IS NULL;

ALTER TABLE dados_crus
    ALTER COLUMN capturado_em SET NOT NULL,
    ALTER COLUMN ignicao DROP NOT NULL,
    ALTER COLUMN bateria DROP NOT NULL;

DROP INDEX dados_crus_veiculo_latest_idx;
DROP INDEX dados_crus_hardware_latest_idx;

CREATE INDEX dados_crus_veiculo_latest_idx
    ON dados_crus (veiculo_id, capturado_em DESC, status_id DESC);

CREATE INDEX dados_crus_hardware_latest_idx
    ON dados_crus (hardware_id, capturado_em DESC, status_id DESC);
