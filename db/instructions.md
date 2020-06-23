# Setup db

1. Create db: `createdb ModMon "DECOVID Model Monitoring"`
2. Create tables: `psql -f schema.sql ModMon`
3. Connect to db: `psql -h localhost -p 5432 ModMon`

# Connect with psqlodbc

1. Install driver for ODBC for PostgreSQL: `brew install psqlodbc`
2. Connect to database with Python (see test_connection.py)

# SQLAlchemy

1. Create schema (if changes to schema.sql): `sqlacodegen postgresql://username@localhost:5432/ModMon --outfile schema.py`
