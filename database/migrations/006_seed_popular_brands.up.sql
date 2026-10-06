INSERT INTO marcas (nome)
VALUES
    ('Fiat'),
    ('Volkswagen'),
    ('Chevrolet'),
    ('Hyundai'),
    ('Toyota'),
    ('Renault'),
    ('Jeep'),
    ('Honda'),
    ('Nissan')
ON CONFLICT DO NOTHING;
