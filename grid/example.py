from app import db
from app.models import Tensor


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "Tensor": Tensor}
