UPDATE hardware
SET ignicao_atual = FALSE
WHERE ignicao_atual IS NULL;

ALTER TABLE hardware
    ALTER COLUMN ignicao_atual SET DEFAULT FALSE,
    ALTER COLUMN ignicao_atual SET NOT NULL,
    ADD COLUMN data_rota_atual DATE,
    ADD COLUMN numero_rota_atual INTEGER,
    ADD CONSTRAINT hardware_rota_atual_pair_check CHECK (
        (data_rota_atual IS NULL AND numero_rota_atual IS NULL)
        OR
        (data_rota_atual IS NOT NULL AND numero_rota_atual > 0)
    );

UPDATE dados_crus
SET ignicao = FALSE
WHERE ignicao IS NULL;

ALTER TABLE dados_crus
    ALTER COLUMN ignicao SET DEFAULT FALSE,
    ALTER COLUMN ignicao SET NOT NULL,
    ADD COLUMN data_rota DATE,
    ADD COLUMN numero_rota INTEGER,
    ADD CONSTRAINT dados_crus_rota_pair_check CHECK (
        (data_rota IS NULL AND numero_rota IS NULL)
        OR
        (data_rota IS NOT NULL AND numero_rota > 0)
    );

CREATE INDEX dados_crus_rota_idx
    ON dados_crus (
        veiculo_id,
        data_rota,
        numero_rota,
        capturado_em,
        status_id
    )
    WHERE numero_rota IS NOT NULL;
