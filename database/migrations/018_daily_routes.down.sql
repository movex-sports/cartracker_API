DROP INDEX dados_crus_rota_idx;

ALTER TABLE dados_crus
    DROP CONSTRAINT dados_crus_rota_pair_check,
    DROP COLUMN numero_rota,
    DROP COLUMN data_rota,
    ALTER COLUMN ignicao DROP DEFAULT,
    ALTER COLUMN ignicao DROP NOT NULL;

ALTER TABLE hardware
    DROP CONSTRAINT hardware_rota_atual_pair_check,
    DROP COLUMN numero_rota_atual,
    DROP COLUMN data_rota_atual,
    ALTER COLUMN ignicao_atual DROP DEFAULT,
    ALTER COLUMN ignicao_atual DROP NOT NULL;
