ALTER TABLE fotos
    RENAME COLUMN foto_url TO object_key;

ALTER TABLE fotos
    RENAME CONSTRAINT fotos_url_not_blank_check
    TO fotos_object_key_not_blank_check;
