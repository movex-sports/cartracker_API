ALTER TABLE locatarios
    ADD COLUMN status BOOLEAN NOT NULL DEFAULT TRUE;

CREATE INDEX locatarios_empresa_status_idx
    ON locatarios (empresa_id, status);
