CREATE TABLE usr (
    id INTEGER NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY
    ,nick TEXT NOT NULL UNIQUE
    ,email TEXT NOT NULL UNIQUE
    ,passwd TEXT NOT NULL
    ,approved BOOLEAN NOT NULL DEFAULT FALSE
    ,code TEXT NOT NULL
    ,code_exp TIMESTAMP NOT NULL
);

CREATE TABLE log (
    id INTEGER NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY
    ,ip TEXT NOT NULL
    ,is_success BOOLEAN NOT NULL
    ,"action" TEXT NOT NULL
    ,timest TIMESTAMP NOT NULL
    ,"log" TEXT NOT NULL
);

CREATE TABLE article_status (
    id INTEGER NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    stat VARCHAR(50) NOT NULL
);

INSERT INTO article_status(stat) VALUES
    ('Submitted'),
    ('Accepted'),
    ('In review'),
    ('Reviewed'),
    ('Rejected'),
    ('Needs Corrections'),
    ('Final');

CREATE TABLE articles (
    id INTEGER NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    author_id INTEGER NOT NULL,
    editor_id INTEGER,
    title VARCHAR(255) NOT NULL,
    content VARCHAR(255) NOT NULL,
    status_id INTEGER NOT NULL REFERENCES article_status(id)
);

CREATE TABLE rounds (
    id INTEGER NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    article_id INT NOT NULL,
    round_number INT NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE TABLE reviews (
    id INTEGER NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    round_id INT NOT NULL,
    reviewer_id INT NOT NULL,
    review_text TEXT,
    status VARCHAR(50) NOT NULL,
    deadline_confirm DATE NOT NULL,
    deadline_submit DATE NOT NULL,
    FOREIGN KEY (round_id) REFERENCES rounds(id)
);

INSERT INTO usr (nick, email, passwd, approved, code, code_exp) VALUES 
('mazimare', 'mazimare0@gmail.com', '$5$rounds=535000$00jq09uCU64jjV2X$TCH6GvPFp5XLIRI1OhwKGU1FgJdSXnlhkMm4qqqooW9', TRUE, '', '2025-02-05 00:31:54.716565');

-- Wstawianie danych do tabeli articles
INSERT INTO articles (title, author_id, content, status_id, editor_id) VALUES 
('Introduction to Flask', 1, 'This is a beginner-friendly guide to Flask.', 1, 1),
('Understanding REST APIs', 2, 'Explores RESTful APIs and their best practices.', 1, 1),
('Advanced Flask Techniques', 3, 'Delves into advanced techniques in Flask.', 1, 1),
('Advanced Flask Techniques2', 3, 'Further techniques in Flask for experienced users.', 1, 1),
('Common Pitfalls', 4, 'Discusses common pitfalls to avoid in Flask.', 1, 1);
