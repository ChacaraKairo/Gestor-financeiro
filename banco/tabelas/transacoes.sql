-- --Tabela: transactions

-- id (BIGINT AUTO_INCREMENT PRIMARY KEY)

-- description (VARCHAR)

-- amount (DECIMAL(10,2))

-- date (DATE)

-- category_id (INT, Foreign Key -> categories.id)

-- is_fixed (BOOLEAN)

-- is_paid (BOOLEAN)

-- payment_method (VARCHAR)

CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    date DATE NOT NULL,
    category_id INT,
    is_fixed BOOLEAN NOT NULL DEFAULT FALSE,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    payment_method VARCHAR(50),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);