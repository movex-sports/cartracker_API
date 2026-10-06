ALTER TABLE users
    ALTER COLUMN role SET DEFAULT '1';

UPDATE users
SET role = '1'
WHERE role = 'user';
