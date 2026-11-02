-- MovieScope schema
-- Run through `python database/init_db.py`, or:
--   mysql -u root -p moviescope < database/schema.sql
--
-- The script is intentionally repeatable: it rebuilds the three demo tables.

DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS movies;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    display_name VARCHAR(80) NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    CONSTRAINT chk_users_name CHECK (CHAR_LENGTH(TRIM(display_name)) > 0)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

CREATE TABLE movies (
    movie_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    title        VARCHAR(150) NOT NULL,
    release_year SMALLINT UNSIGNED NOT NULL,
    genre        VARCHAR(40) NOT NULL,
    poster_url   VARCHAR(500) NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (movie_id),
    INDEX idx_movies_genre (genre),
    INDEX idx_movies_year (release_year),
    CONSTRAINT chk_movies_title CHECK (CHAR_LENGTH(TRIM(title)) > 0),
    CONSTRAINT chk_movies_year CHECK (release_year BETWEEN 1888 AND 2100)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

CREATE TABLE ratings (
    rating_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id   INT UNSIGNED NOT NULL,
    movie_id  INT UNSIGNED NOT NULL,
    rating    TINYINT UNSIGNED NOT NULL,
    rated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
              ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (rating_id),
    UNIQUE KEY uq_ratings_user_movie (user_id, movie_id),
    INDEX idx_ratings_movie (movie_id),
    CONSTRAINT fk_ratings_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ratings_movie
        FOREIGN KEY (movie_id) REFERENCES movies (movie_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_ratings_value CHECK (rating BETWEEN 1 AND 10)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;
