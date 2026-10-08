ALTER TABLE fotos
    RENAME CONSTRAINT fotos_object_key_not_blank_check
    TO fotos_url_not_blank_check;

ALTER TABLE fotos
    RENAME COLUMN object_key TO foto_url;
