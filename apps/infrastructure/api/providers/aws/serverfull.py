from .aws import *
from .utils import base_setup


class AWS_Serverfull(AWS):
    def __init__(self, config, credentials, vpc_config) -> None:
        """
        credentials (dict) : Contains AWS credentials
        vpc_config (dict) : Contains arguments required to deploy the VPC
        db_config (dict) : Contains username and password of the deployed database
        app_config (dict) : Contains arguments which are required to deploy the app.
        """

        super().__init__(config, credentials, vpc_config)

        self.build()

    # TODO: Amr add outputs function, which appends outputs to self.tfscript.
    # the parent class handles returing the output as a response from the API.
    def build(self):
        # ----- Security Group ------#

        self.security_group = resource.aws_security_group(
            "security_group",
            name="pygrid-security-group",
            vpc_id=var(self.vpc.id),
            ingress=[
                {
                    "description": "HTTPS",
                    "from_port": 443,
                    "to_port": 443,
                    "protocol": "tcp",
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": ["::/0"],
                    "prefix_list_ids": [],
                    "security_groups": [],
                    "self": True,
                },
                {
                    "description": "HTTP",
                    "from_port": 80,
                    "to_port": 80,
                    "protocol": "tcp",
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": ["::/0"],
                    "prefix_list_ids": [],
                    "security_groups": [],
                    "self": True,
                },
                {
                    "description": "PyGrid Nodes",
                    "from_port": 5000,
                    "to_port": 5999,
                    "protocol": "tcp",
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": ["::/0"],
                    "prefix_list_ids": [],
                    "security_groups": [],
                    "self": True,
                },
                {
                    "description": "PyGrid Workers",
                    "from_port": 6000,
                    "to_port": 6999,
                    "protocol": "tcp",
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": ["::/0"],
                    "prefix_list_ids": [],
                    "security_groups": [],
                    "self": True,
                },
                {
                    "description": "PyGrid Networks",
                    "from_port": 7000,
                    "to_port": 7999,
                    "protocol": "tcp",
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": ["::/0"],
                    "prefix_list_ids": [],
                    "security_groups": [],
                    "self": True,
                },
            ],
            egress=[
                {
                    "description": "Egress Connection",
                    "from_port": 0,
                    "to_port": 0,
                    "protocol": "-1",
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": ["::/0"],
                    "prefix_list_ids": [],
                    "security_groups": [],
                    "self": True,
                }
            ],
            tags={"Name": "pygrid-security-group"},
        )
        self.tfscript += self.security_group

    def deploy_network(self):
        self.ami = terrascript.data.aws_ami(
            "ubuntu",
            most_recent=True,
            filter=[
                {
                    "name": "name",
                    "values": [
                        "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"
                    ],
                },
                {"name": "virtualization-type", "values": ["hvm"]},
            ],
            owners=["099720109477"],
        )
        self.tfscript += self.ami

        self.instance = terrascript.resource.aws_instance(
            f"PyGridNetworkInstance",
            ami=var(self.ami.id),
            instance_type=self.config.vpc.instance_type,
            associate_public_ip_address=True,
            vpc_security_group_ids=[var(self.security_group.id)],
            subnet_id=var(self.subnets[0][1].id),
            user_data=f"""
                {base_setup}
                cd /PyGrid/apps/network
                poetry install
                nohup ./run.sh --port {self.config.app.port}  --host {self.config.app.host}
            """,
        )
        self.tfscript += self.instance

    def deploy_node(self):
        self.ami = terrascript.data.aws_ami(
            "ubuntu",
            most_recent=True,
            filter=[
                {
                    "name": "name",
                    "values": [
                        "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"
                    ],
                },
                {"name": "virtualization-type", "values": ["hvm"]},
            ],
            owners=["099720109477"],
        )
        self.tfscript += self.ami

        self.instance = terrascript.resource.aws_instance(
            f"PyGridNodeInstance",
            ami=var(self.ami.id),
            instance_type=self.config.vpc.instance_type,
            associate_public_ip_address=True,
            vpc_security_group_ids=[var(self.security_group.id)],
            subnet_id=var(self.subnets[0][1].id),
            key_name="openmined_pygrid",
            user_data=f"""
                {base_setup}
                cd /PyGrid/apps/node
                poetry install
                nohup ./run.sh --id {self.config.app.id} --port {self.config.app.port}  --host {self.config.app.host} --network {self.config.app.network}
            """,
        )
        self.tfscript += self.instance
