#!/bin/env python
from app import create_app
import sys

app = create_app(debug=True)

if __name__ == "__main__":
    app.run()
