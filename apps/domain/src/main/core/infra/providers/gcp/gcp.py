from ..provider import *
from ..terraform import generate_cidr_block, var, var_module


class GCP(Provider):
    """Google Cloud Provider."""

    def __init__(self, config: SimpleNamespace) -> None:
        super().__init__(config)

        self.tfscript += terrascript.provider.google(
            project=self.config.gcp.project_id,
            region=self.config.gcp.region,
            zone=self.config.gcp.zone,
        )

        ##TODO(amr): Build the Infrastructure
        self.build_infra()

        self.build_instances()
        self.build_load_balancer()

        self.output()

    def output(self):
        ##TODO(amr): move this to output function
        self.tfscript += terrascript.output(
            f"instance_ip_endpoint",
            # value="${" + self.pygrid_ip.address + "}",
            value=var_module(self.pygrid_ip, "address"),
            description=f"The public IP address of gcp instance.",
        )

    def build_infra(self):
        app = self.config.app.name
        self.firewall = resource.google_compute_firewall(
            f"firewall_{app}",
            name=f"firewall_{app}",
            network="default",
            allow={
                "protocol": "tcp",
                "ports": ["80", "443", "5000-5999", "6000-6999", "7000-7999"],
            },
        )
        self.tfscript += self.firewall

        self.pygrid_ip = resource.google_compute_address(
            f"pygrid-{app}",
            name=f"pygrid-{app}",
        )
        self.tfscript += self.pygrid_ip

    def build_instances(self):
        ##TODO(amr): https://registry.terraform.io/modules/terraform-google-modules/vm/google/latest/submodules/instance_template
        pass

    def build_load_balancer(self):
        ##TODO(amr): https://github.com/gruntwork-io/terraform-google-load-balancer
        pass
