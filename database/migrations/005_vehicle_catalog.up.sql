CREATE TABLE marcas (
    marca_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(80) NOT NULL
);

CREATE UNIQUE INDEX marcas_nome_unique_idx ON marcas (LOWER(nome));

CREATE TABLE modelos (
    modelo_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    marca_id BIGINT NOT NULL,
    nome VARCHAR(100) NOT NULL,

    CONSTRAINT modelos_marca_fk
        FOREIGN KEY (marca_id) REFERENCES marcas (marca_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE UNIQUE INDEX modelos_marca_nome_unique_idx
    ON modelos (marca_id, LOWER(nome));
CREATE INDEX modelos_marca_id_idx ON modelos (marca_id);
