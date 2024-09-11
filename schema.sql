DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS habit_boards;
DROP TABLE IF EXISTS habits;
DROP TABLE IF EXISTS habit_options;
DROP TABLE IF EXISTS entries;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE habit_boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    board_type TEXT NOT NULL CHECK(board_type IN ('time-series', 'batch')),
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    board_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    frequency TEXT, -- can be NULL for batch habits
    variable_type TEXT NOT NULL CHECK(variable_type IN ('boolean', 'numeric', 'categorical')),
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (board_id) REFERENCES habit_boards (id)
);

CREATE TABLE habit_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    option_value TEXT NOT NULL,
    FOREIGN KEY (habit_id) REFERENCES habits (id)
);

CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    date DATE NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (habit_id) REFERENCES habits (id)
);