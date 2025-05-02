#!/bin/bash

set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=1
while ! nc -z db 5432; do
    if [ $attempt -eq $max_attempts ]; then
        echo "Error: PostgreSQL not available after $max_attempts attempts"
        exit 1
    fi
    echo "Attempt $attempt: PostgreSQL not ready, waiting..."
    sleep 2
    attempt=$((attempt + 1))
done
echo "PostgreSQL is ready!"

# Create database tables
echo "Creating database tables..."
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    try:
        db.create_all()
        print('Database tables created successfully')
    except Exception as e:
        print(f'Error creating database tables: {str(e)}')
        raise
"

# Start the application
echo "Starting application..."
exec "$@" 