CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    sobrenome VARCHAR(150) NOT NULL,
    cpf VARCHAR(11) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL,
    rua VARCHAR(150),
    numero VARCHAR(20),
    cep VARCHAR(8),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    contato VARCHAR(20),
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_owner BOOLEAN NOT NULL DEFAULT FALSE,
    status BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT users_cpf_format_check CHECK (cpf ~ '^[0-9]{11}$'),
    CONSTRAINT users_email_format_check CHECK (email = BTRIM(email) AND POSITION('@' IN email) > 1),
    CONSTRAINT users_cep_format_check CHECK (cep IS NULL OR cep ~ '^[0-9]{8}$'),
    CONSTRAINT users_estado_format_check CHECK (estado IS NULL OR estado ~ '^[A-Z]{2}$'),
    CONSTRAINT users_username_not_blank_check CHECK (BTRIM(username) <> ''),
    CONSTRAINT users_role_not_blank_check CHECK (BTRIM(role) <> '')
);

CREATE UNIQUE INDEX users_email_unique_idx ON users (LOWER(email));

CREATE TABLE veiculos (
    veiculo_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    marca VARCHAR(80) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    ano SMALLINT NOT NULL,
    cor VARCHAR(50),
    placa VARCHAR(7) NOT NULL UNIQUE,
    combustivel_tipo VARCHAR(30) NOT NULL,
    capacidade_tanque_l NUMERIC(7,2),
    consumo_km_l NUMERIC(7,2),
    velocidade_maxima_kmh NUMERIC(7,2),
    odometro_km NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT veiculos_owner_fk
        FOREIGN KEY (owner_id) REFERENCES users (user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT veiculos_ano_check CHECK (ano BETWEEN 1886 AND 2200),
    CONSTRAINT veiculos_placa_format_check CHECK (placa ~ '^[A-Z0-9]{7}$'),
    CONSTRAINT veiculos_capacidade_tanque_check
        CHECK (capacidade_tanque_l IS NULL OR capacidade_tanque_l > 0),
    CONSTRAINT veiculos_consumo_check
        CHECK (consumo_km_l IS NULL OR consumo_km_l > 0),
    CONSTRAINT veiculos_velocidade_maxima_check
        CHECK (velocidade_maxima_kmh IS NULL OR velocidade_maxima_kmh > 0),
    CONSTRAINT veiculos_odometro_check CHECK (odometro_km >= 0)
);

CREATE INDEX veiculos_owner_id_idx ON veiculos (owner_id);

CREATE TABLE fotos (
    foto_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    veiculo_id BIGINT NOT NULL,
    foto_url TEXT NOT NULL,
    thumb BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fotos_veiculo_fk
        FOREIGN KEY (veiculo_id) REFERENCES veiculos (veiculo_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fotos_url_not_blank_check CHECK (BTRIM(foto_url) <> '')
);

CREATE INDEX fotos_veiculo_id_idx ON fotos (veiculo_id);

-- Cada veiculo pode ter no maximo uma foto marcada como miniatura.
CREATE UNIQUE INDEX fotos_veiculo_thumb_unique_idx
    ON fotos (veiculo_id)
    WHERE thumb = TRUE;
