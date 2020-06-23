1. Create db: `createdb ModMon "DECOVID Model Monitoring"`
2. Create tables: `psql -f schema.sql ModMon`
3. Connect to db: `psql -h localhost -p 5432 ModMon`
4. Install driver for ODBC for PostgreSQL: `brew install psqlodbc`
5. Connect to database with Python (see test_connection.py)
