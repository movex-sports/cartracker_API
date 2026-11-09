ALTER TABLE hardware
    ADD COLUMN ignicao_atual BOOLEAN,
    ADD COLUMN ignicao_atualizada_em TIMESTAMPTZ,
    ADD COLUMN ultimo_heartbeat_em TIMESTAMPTZ;
