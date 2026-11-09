DROP INDEX dados_crus_hardware_latest_idx;
DROP INDEX dados_crus_veiculo_latest_idx;

CREATE INDEX dados_crus_veiculo_latest_idx
    ON dados_crus (veiculo_id, registrado_em DESC, status_id DESC);

CREATE INDEX dados_crus_hardware_latest_idx
    ON dados_crus (hardware_id, registrado_em DESC, status_id DESC);

UPDATE dados_crus
SET ignicao = FALSE, bateria = 0
WHERE ignicao IS NULL OR bateria IS NULL;

ALTER TABLE dados_crus
    ALTER COLUMN ignicao SET NOT NULL,
    ALTER COLUMN bateria SET NOT NULL,
    DROP COLUMN capturado_em;
