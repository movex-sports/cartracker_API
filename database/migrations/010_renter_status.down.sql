DROP INDEX locatarios_empresa_status_idx;

ALTER TABLE locatarios
    DROP COLUMN status;
