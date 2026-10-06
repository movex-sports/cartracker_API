WITH seed (marca_nome, modelo_nome) AS (
    VALUES
        ('Fiat', 'Mobi'),
        ('Fiat', 'Argo'),
        ('Fiat', 'Cronos'),
        ('Fiat', 'Strada'),
        ('Fiat', 'Fiorino'),
        ('Fiat', 'Pulse'),
        ('Volkswagen', 'Gol'),
        ('Volkswagen', 'Polo'),
        ('Volkswagen', 'Voyage'),
        ('Volkswagen', 'Virtus'),
        ('Volkswagen', 'Saveiro'),
        ('Volkswagen', 'T-Cross'),
        ('Chevrolet', 'Onix'),
        ('Chevrolet', 'Onix Plus'),
        ('Chevrolet', 'Prisma'),
        ('Chevrolet', 'Spin'),
        ('Chevrolet', 'Tracker'),
        ('Chevrolet', 'Montana'),
        ('Hyundai', 'HB20'),
        ('Hyundai', 'HB20S'),
        ('Hyundai', 'Creta'),
        ('Toyota', 'Etios'),
        ('Toyota', 'Yaris'),
        ('Toyota', 'Yaris Sedan'),
        ('Toyota', 'Corolla'),
        ('Renault', 'Kwid'),
        ('Renault', 'Sandero'),
        ('Renault', 'Logan'),
        ('Renault', 'Duster'),
        ('Renault', 'Kardian'),
        ('Renault', 'Oroch'),
        ('Jeep', 'Renegade'),
        ('Honda', 'Fit'),
        ('Honda', 'City'),
        ('Honda', 'City Hatchback'),
        ('Nissan', 'March'),
        ('Nissan', 'Versa'),
        ('Nissan', 'Kicks')
)
INSERT INTO modelos (marca_id, nome)
SELECT marca.marca_id, seed.modelo_nome
FROM seed
INNER JOIN marcas AS marca
    ON LOWER(marca.nome) = LOWER(seed.marca_nome)
ON CONFLICT DO NOTHING;
