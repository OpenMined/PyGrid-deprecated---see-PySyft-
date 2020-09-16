# Add dependencies in EFS to python-path
import os
import sys

sys.path.append(os.environ.get("MOUNT_PATH"))

from app import create_lambda_app

app = create_lambda_app(node_id="bob")
