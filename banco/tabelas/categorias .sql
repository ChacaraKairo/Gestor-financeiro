-- Tabela: categories

-- id (INT AUTO_INCREMENT PRIMARY KEY)

-- name (VARCHAR)

-- color_hex (VARCHAR)

-- type (ENUM 'receita', 'despesa')

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    color_hex VARCHAR(7),
    type ENUM('receita', 'despesa') NOT NULL
);