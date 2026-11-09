DROP INDEX dados_crus_hardware_latest_idx;

ALTER TABLE dados_crus
    DROP CONSTRAINT dados_crus_hardware_fk,
    DROP COLUMN hardware_id;

ALTER TABLE hardware
    DROP COLUMN status;
