DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS habits;
DROP TABLE IF EXISTS entries;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    board_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    frequency TEXT NOT NULL,
    variable_type TEXT NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (board_id) REFERENCES habit_boards (id)
);

CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    date DATE NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (habit_id) REFERENCES habits (id)
);

CREATE TABLE habit_boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);