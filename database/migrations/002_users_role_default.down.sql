UPDATE users
SET role = 'user'
WHERE role = '1';

ALTER TABLE users
    ALTER COLUMN role SET DEFAULT 'user';
