#!/bin/bash
exec gunicorn -k flask_sockets.worker grid:app \
"$@"
