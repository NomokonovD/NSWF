\c ptstart_bot

CREATE ROLE repl_user WITH REPLICATION LOGIN ENCRYPTED PASSWORD 'Qq12345';
SELECT pg_create_physical_replication_slot('replication_slot');

CREATE TABLE email_addresses (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL
);

CREATE TABLE phone_numbers (
  id SERIAL PRIMARY KEY,
  phone_number VARCHAR(20) NOT NULL
);

INSERT INTO email_addresses (email) VALUES ('ptuser1@ptsecurity.com'), ('ptuser2@ptsecurity.com');

INSERT INTO phone_numbers (phone_number) VALUES ('+1234567890'), ('+0987654321');
