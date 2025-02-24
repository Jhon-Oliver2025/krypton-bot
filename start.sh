#!/bin/bash
pip install gunicorn
python monitor.py &
gunicorn run:server