DROP INDEX hardware_imei_unique_idx;

ALTER TABLE hardware
    DROP CONSTRAINT hardware_imei_format_check,
    DROP COLUMN imei;
