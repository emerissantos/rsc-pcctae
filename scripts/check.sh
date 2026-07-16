#!/usr/bin/env sh
set -eu
python -m compileall -q apps config manage.py
python manage.py check
