CREATE TABLE dados_crus (
    status_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    veiculo_id BIGINT NOT NULL,
    ignicao BOOLEAN NOT NULL,
    bateria NUMERIC(10, 2) NOT NULL,
    velocidade NUMERIC(8, 2) NOT NULL,
    longitude NUMERIC(11, 7) NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    registrado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT dados_crus_veiculo_fk
        FOREIGN KEY (veiculo_id) REFERENCES veiculos (veiculo_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT dados_crus_bateria_nonnegative_check
        CHECK (bateria >= 0),
    CONSTRAINT dados_crus_velocidade_nonnegative_check
        CHECK (velocidade >= 0),
    CONSTRAINT dados_crus_longitude_range_check
        CHECK (longitude BETWEEN -180 AND 180),
    CONSTRAINT dados_crus_latitude_range_check
        CHECK (latitude BETWEEN -90 AND 90)
);

CREATE INDEX dados_crus_veiculo_latest_idx
    ON dados_crus (veiculo_id, registrado_em DESC, status_id DESC);
