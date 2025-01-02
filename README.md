### RDMS Commands:

**Schema Creation**

```bash
psql -h <db_host> -p <db_port> -U <db_user> -d <db_name>

```

```sql

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    task_id INT REFERENCES tasks(id),
    performed_by INT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (username, email) VALUES ('test_user', 'test_user@example.com');

```
