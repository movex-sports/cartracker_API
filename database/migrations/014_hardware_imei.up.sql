ALTER TABLE hardware
    ADD COLUMN imei VARCHAR(16);

ALTER TABLE hardware
    ADD CONSTRAINT hardware_imei_format_check
        CHECK (imei IS NULL OR imei ~ '^[0-9]{14,16}$');

CREATE UNIQUE INDEX hardware_imei_unique_idx
    ON hardware (imei)
    WHERE imei IS NOT NULL;
