#!/bin/bash
source venv/bin/activate

# Server
exec gunicorn -b :5000 --access-logfile - --error-logfile - main:app