import subprocess
import textwrap

import click
from PyInquirer import prompt

from ...tf import generate_cidr_block, var, var_module
from ..provider import *
from .azure_ts import *


class AZURE(Provider):
    """Azure Cloud Provider."""

    def __init__(self, config: SimpleNamespace) -> None:
        super().__init__(config.root_dir, "azure")

        self.config = config

        ##TODO(amr): terrascript does not support azurem right now
        self.tfscript += terrascript.terraform(backend=terrascript.backend("azurerm"))
        self.tfscript += azurerm(
            features={},
            subscription_id=self.config.azure.subscription_id,
            client_id=self.config.azure.client_id,
            client_secret=self.config.azure.client_secret,
            tenant_id=self.config.azure.tenant_id,
        )

        self.build()
        self.build_instances()
        print(self.tfscript)

    def build(self) -> bool:
        self.resource_group = azurerm_resource_group(
            "pygrid_resource_group",
            name="pygrid_resource_group",
            location=self.config.azure.location,
        )
        self.tfscript += self.resource_group

        self.virtual_network = azurerm_virtual_network(
            f"pygrid_virtual_network",
            name=f"pygrid_virtual_network",
            resource_group_name=self.resource_group.name,
            location=self.resource_group.location,
            address_space=["10.0.0.0/16"],
            tags={
                "name": "pygrid-virtual-network",
                "environment": "dev",
            },
        )
        self.tfscript += self.virtual_network

        self.azurerm_subnet = azurerm_subnet(
            f"pygrid_subnet",
            name=f"pygrid_subnet",
            resource_group_name=self.resource_group.name,
            virtual_network_name=self.virtual_network.name,
            address_prefixes=["10.0.2.0/24"],
        )
        self.tfscript += self.azurerm_subnet

        self.network_interface = azurerm_network_interface(
            f"pygrid_network_interface",
            name=f"pygrid_network_interface",
            resource_group_name=self.resource_group.name,
            location=self.resource_group.location,
            ip_configuration={
                "name": "internal",
                "subnet_id": self.azurerm_subnet.id,
                "private_ip_address_allocation": "Dynamic",
            },
        )
        self.tfscript += self.network_interface

        self.network_security_group = azurerm_network_security_group(
            f"pygrid-network-security-group",
            name=f"pygrid-network-security-group",
            resource_group_name=self.resource_group.name,
            location=self.resource_group.location,
            security_rule=[
                {
                    "name": "HTTPS",
                    "priority": 100,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": "Tcp",
                    "source_port_range": "443",
                    "destination_port_range": "443",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                },
                {
                    "name": "HTTP",
                    "priority": 100,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": "Tcp",
                    "source_port_range": "80",
                    "destination_port_range": "80",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                },
                {
                    "name": "PyGrid Domains",
                    "priority": 100,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": "Tcp",
                    "source_port_range": "5000",
                    "destination_port_range": "5999",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                },
                {
                    "name": "PyGrid Workers",
                    "priority": 100,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": "Tcp",
                    "source_port_range": "6000",
                    "destination_port_range": "6999",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                },
                {
                    "name": "PyGrid Networks",
                    "priority": 100,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": "Tcp",
                    "source_port_range": "7000",
                    "destination_port_range": "7999",
                    "source_address_prefix": "*",
                    "destination_address_prefix": "*",
                },
            ],
        )
        self.tfscript += self.network_security_group

    def build_instances(self):
        name = self.config.app.name

        self.instances = []
        for count in range(self.config.app.count):
            app = self.config.apps[count]

            instance = azurerm_virtual_machine(
                name,
                name=name,
                resource_group_name=self.resource_group.name,
                location=self.resource_group.location,
                network_interface_ids=[self.network_interface.id],
                vm_size="Standard_DS1_v2",  # TODO: get this config from user
                # TODO: get config from user
                storage_image_reference={
                    "publisher": "Canonical",
                    "offer": "UbuntuServer",
                    "sku": "16.04-LTS",
                    "version": "latest",
                },
                storage_os_disk={
                    "name": "myosdisk1",
                    "caching": "ReadWrite",
                    "create_option": "FromImage",
                    "managed_disk_type": "Standard_LRS",
                },
                os_profile={
                    "computer_name": "hostname",
                    "admin_username": "testadmin",
                    "admin_password": "Password1234!",
                },
                os_profile_linux_config={"disable_password_authentication": False},
                custom_data=self.write_exec_script(app, index=count),
            )

            self.tfscript += instance
            self.instances.append(instance)

    def write_exec_script(self, app, index=0):
        ##TODO(amr): remove `git checkout pygrid_0.3.0` after merge

        # exec_script = "#cloud-boothook\n#!/bin/bash\n"
        exec_script = "#!/bin/bash\n"
        exec_script += textwrap.dedent(
            f"""
            ## For debugging
            # redirect stdout/stderr to a file
            exec &> logs.out

            echo 'Simple Web Server for testing the deployment'
            sudo apt update -y
            sudo apt install apache2 -y
            sudo systemctl start apache2
            echo '<h1>OpenMined {self.config.app.name} Server ({index}) Deployed via Terraform</h1>' | sudo tee /var/www/html/index.html

            echo 'Setup Miniconda environment'
            sudo wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
            sudo bash miniconda.sh -b -p miniconda
            sudo rm miniconda.sh
            export PATH=/miniconda/bin:$PATH > ~/.bashrc
            conda init bash
            source ~/.bashrc
            conda create -y -n pygrid python=3.7
            conda activate pygrid

            echo 'Install poetry...'
            pip install poetry

            echo 'Install GCC'
            sudo apt-get install python3-dev -y
            sudo apt-get install libevent-dev -y
            sudo apt-get install gcc -y

            echo 'Cloning PyGrid'
            git clone https://github.com/OpenMined/PyGrid && cd /PyGrid/
            git checkout pygrid_0.4.0

            cd /PyGrid/apps/{self.config.app.name}

            echo 'Installing {self.config.app.name} Dependencies'
            poetry install

            ## TODO(amr): remove this after poetry updates
            pip install pymysql

            nohup ./run.sh --port {app.port}  --host {app.host}
        """
        )
        return exec_script
