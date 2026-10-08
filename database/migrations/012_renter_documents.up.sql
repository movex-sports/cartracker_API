CREATE TABLE documentos_locatarios (
    documento_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    locatario_id BIGINT NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'cnh',
    object_key TEXT NOT NULL,
    nome_original VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT documentos_locatarios_locatario_fk
        FOREIGN KEY (locatario_id) REFERENCES locatarios (locatario_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT documentos_locatarios_tipo_check
        CHECK (tipo = 'cnh'),
    CONSTRAINT documentos_locatarios_object_key_not_blank_check
        CHECK (BTRIM(object_key) <> ''),
    CONSTRAINT documentos_locatarios_nome_not_blank_check
        CHECK (BTRIM(nome_original) <> ''),
    CONSTRAINT documentos_locatarios_cnh_unique
        UNIQUE (locatario_id, tipo)
);

CREATE INDEX documentos_locatarios_locatario_id_idx
    ON documentos_locatarios (locatario_id);
