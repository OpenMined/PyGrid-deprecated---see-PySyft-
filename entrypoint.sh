#!/bin/bash
exec gunicorn -k flask_sockets.worker "grid:create_app()" \
"$@"
