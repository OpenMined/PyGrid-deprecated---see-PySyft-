import click

from ..deploy import base_setup
from ..tf import *
from ..utils import Config
from .provider import *


class GCP(Provider):
    """Google Cloud Provider."""

    def __init__(self, config):
        super().__init__(config)

        self.config.gcp = self.get_gcp_config()

        self.tfscript += terrascript.provider.google(
            credentials=self.config.gcp.credentials,
            project=self.config.gcp.project_id,
            region=self.config.gcp.region,
        )

        self.update_script()

        click.echo("Initializing GCP Provider")
        TF.init()

        build = self.build()

        if build == 0:
            click.echo("Main Infrastructure has built Successfully!\n\n")

    def build(self) -> bool:
        self.firewall = terrascript.resource.google_compute_firewall(
            "firewall",
            name="firewall",
            network="default",
            allow={
                "protocol": "tcp",
                "ports": ["80", "443", "5000-5999", "6000-6999", "7000-7999",],
            },
        )
        self.tfscript += self.firewall

        self.pygrid_ip = terrascript.resource.google_compute_address(
            "pygrid", name="pygrid",
        )
        self.tfscript += self.pygrid_ip

        self.tfscript += terrascript.output(
            "pygrid_ip", value="${" + self.pygrid_ip.address + "}",
        )

        self.update_script()
        return TF.validate()

    def deploy_network(
        self, name: str = "PyGridNetwork", apply: bool = True,
    ):
        image = terrascript.data.google_compute_image(
            name + "container-optimized-os", family="cos-81-lts", project="cos-cloud",
        )
        self.tfscript += image

        network = terrascript.resource.google_compute_instance(
            name,
            name=name,
            machine_type="",  # TODO: machine_type,
            zone="",  # TODO: zone,
            boot_disk={"initialize_params": {"image": "${" + image.self_link + "}"}},
            network_interface={
                "network": "default",
                "access_config": {"nat_ip": "${" + self.pygrid_ip.address + "}"},
            },
            metadata_startup_script=f"""
                {base_setup}
                cd /PyGrid/apps/network
                poetry install
                nohup ./run.sh --port {self.config.app.port}  --host {self.config.app.host} {'--start_local_db' if self.config.app.start_local_db else ''}
            """,
        )
        self.tfscript += network

        self.update_script()

    def deploy_node(
        self, name: str = "PyGridNode", apply: bool = True,
    ):
        image = terrascript.data.google_compute_image(
            name + "container-optimized-os", family="cos-81-lts", project="cos-cloud",
        )
        self.tfscript += image

        network = terrascript.resource.google_compute_instance(
            name,
            name=name,
            machine_type="",  # TODO:  machine_type,
            zone="",  # TODO: zone,
            boot_disk={"initialize_params": {"image": "${" + image.self_link + "}"}},
            network_interface={"network": "default", "access_config": {},},
            metadata_startup_script=f"""
                {base_setup}
                cd /PyGrid/apps/node
                poetry install
                nohup ./run.sh --id {self.config.app.id} --port {self.config.app.port}  --host {self.config.app.host} --network {self.config.app.network} --num_replicas {self.config.app.num_replicas} {'--start_local_db' if self.config.app.start_local_db else ''}
            """,
        )
        self.tfscript += network

        self.update_script()

    def get_gcp_config(self) -> Config:
        """Getting the configration required for deployment on GCP.

        Returns:
            Config: Simple Config with the user inputs
        """
        ## TODO: promt user for configs

        return Config(region="", credentials="", project_id="",)
