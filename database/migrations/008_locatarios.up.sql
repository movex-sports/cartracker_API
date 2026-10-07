CREATE UNIQUE INDEX veiculos_id_empresa_unique_idx
    ON veiculos (veiculo_id, empresa_id);

CREATE TABLE locatarios (
    locatario_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    empresa_id BIGINT NOT NULL,
    veiculo_id BIGINT NOT NULL,
    locatario_nome VARCHAR(100) NOT NULL,
    locatario_sobrenome VARCHAR(150) NOT NULL,
    locatario_cpf VARCHAR(11) NOT NULL,
    locatario_rua VARCHAR(150) NOT NULL,
    locatario_numero VARCHAR(20) NOT NULL,
    locatario_cep VARCHAR(8) NOT NULL,
    locatario_bairro VARCHAR(100) NOT NULL,
    locatario_cidade VARCHAR(100) NOT NULL,
    locatario_estado VARCHAR(2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT locatarios_empresa_fk
        FOREIGN KEY (empresa_id) REFERENCES empresas (empresa_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT locatarios_veiculo_empresa_fk
        FOREIGN KEY (veiculo_id, empresa_id)
        REFERENCES veiculos (veiculo_id, empresa_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT locatarios_cpf_format_check
        CHECK (locatario_cpf ~ '^[0-9]{11}$'),
    CONSTRAINT locatarios_cep_format_check
        CHECK (locatario_cep ~ '^[0-9]{8}$'),
    CONSTRAINT locatarios_estado_format_check
        CHECK (locatario_estado ~ '^[A-Z]{2}$')
);

CREATE INDEX locatarios_empresa_id_idx ON locatarios (empresa_id);
CREATE INDEX locatarios_veiculo_id_idx ON locatarios (veiculo_id);
CREATE INDEX locatarios_empresa_cpf_idx
    ON locatarios (empresa_id, locatario_cpf);
