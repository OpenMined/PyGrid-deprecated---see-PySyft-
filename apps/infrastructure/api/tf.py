import json
import subprocess

var = lambda x: "${" + x + "}"
var_module = lambda x, y: var(f"module.{x._name}.{y}")


class Terraform:
    def __init__(self):
        super().__init__()

    def init(self, dir):
        return subprocess.run("terraform init", shell=True, cwd=dir, check=True)

    def validate(self, dir):
        return subprocess.run("terraform validate", shell=True, cwd=dir, check=True)

    def plan(self, dir):
        return subprocess.run("terraform plan", shell=True, cwd=dir, check=True)

    def apply(self, dir):
        return subprocess.run(
            "terraform apply --auto-approve", shell=True, cwd=dir, check=True
        )

    def output(self, dir):
        output = subprocess.run(
            "terraform output -json",
            shell=True,
            cwd=dir,
            check=True,
            stdout=subprocess.PIPE,
        )
        return json.loads(output.stdout.decode("utf-8"))

    def destroy(self, dir):
        return subprocess.run("terraform destroy", shell=True, cwd=dir, check=True)
