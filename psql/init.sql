CREATE TABLE log (
    id INTEGER NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY
    ,ip TEXT NOT NULL
    ,is_success BOOLEAN NOT NULL
    ,"action" TEXT NOT NULL
    ,timest TIMESTAMP NOT NULL
    ,"log" TEXT NOT NULL
);

CREATE TABLE articles (
    id INTEGER NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    content VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL
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

-- Wstawianie danych do tabeli articles
INSERT INTO articles (title, author, content, status) VALUES 
('Introduction to Flask', 'John Doe', 'This is a beginner-friendly guide to Flask.', 'Submitted'),
('Understanding REST APIs', 'Jane Smith', 'Explores RESTful APIs and their best practices.', 'Submitted'),
('Advanced Flask Techniques', 'Alice Johnson', 'Delves into advanced techniques in Flask.', 'Submitted'),
('Advanced Flask Techniques2', 'Alice Johnson', 'Further techniques in Flask for experienced users.', 'Submitted'),
('Common Pitfalls', 'Bob Brown', 'Discusses common pitfalls to avoid in Flask.', 'Submitted');
