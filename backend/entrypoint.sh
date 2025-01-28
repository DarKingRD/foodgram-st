#!/bin/sh

# Run migrations and collect static files
python manage.py migrate
python manage.py collectstatic --noinput

# Optionally load test data
if [ "$LOAD_TEST_DATA" = "1" ]; then
    echo "Loading test data..."
    python manage.py loaddata test_data.json
else
    echo "Skipping test data loading."
fi

# Start Gunicorn server
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3