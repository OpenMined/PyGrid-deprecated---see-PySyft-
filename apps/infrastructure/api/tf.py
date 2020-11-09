import subprocess

var = lambda x: "${" + x + "}"
var_module = lambda x, y: var(f"module.{x._name}.{y}")


class Terraform:
    def __init__(self) -> None:
        super().__init__()

    def init(self, dir: str):
        return subprocess.call("terraform init", shell=True, cwd=dir)

    def validate(self, dir: str):
        return subprocess.call("terraform validate", shell=True, cwd=dir)

    def plan(self, dir: str):
        return subprocess.call("terraform plan", shell=True, cwd=dir)

    def apply(self, dir: str):
        return subprocess.call("terraform apply", shell=True, cwd=dir)

    def destroy(self, dir: str):
        return subprocess.call("terraform destroy", shell=True, cwd=dir)
