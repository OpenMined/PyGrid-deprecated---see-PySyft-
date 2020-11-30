from ...tf import var
from .aws import *


class AWS_Serverfull(AWS):
    def __init__(self, config) -> None:
        """
        credentials (dict) : Contains AWS credentials
        """

        super().__init__(config)

        self.build_security_group()
        self.writing_exec_script()
        self.build_instance()

        self.output()

    def output(self):
        self.tfscript += terrascript.Output(
            "instance_endpoint",
            value=var(self.instance.public_ip),
            description="The public IP address of the main server instance.",
        )

    def build_security_group(self):
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

    def build_instance(self):
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

        self.instances = Module(
            f"pygrid-cluster",
            instance_count=2,  ## TODO: get config.count
            source="terraform-aws-modules/ec2-instance/aws",
            name=f"pygrid-{self.config.app.name}-instances",
            ami=var(self.ami.id),
            instance_type=self.config.vpc.instance_type,
            associate_public_ip_address=True,
            monitoring=True,
            vpc_security_group_ids=[var(self.security_group.id)],
            subnet_ids=[var(public_subnet.id) for _, public_subnet in self.subnets],
            user_data=f"file('{self.root_dir}/deploy.sh')",
            tags={
                "Name": f"pygrid-{self.config.app.name}-instances",
            },
        )
        self.tfscript += self.instances
        )
        self.tfscript += self.instance

    def writing_exec_script(self):
        exec_script = f'''
        #!/bin/bash

        ## For debugging
        # redirect stdout/stderr to a file
        exec &> log.out


        echo "Simple Web Server for testing the deployment"
        sudo apt update -y
        sudo apt install apache2 -y
        sudo systemctl start apache2
        echo """
        <h1 style='color:#f09764; text-align:center'>
            OpenMined First Server Deployed via Terraform
        </h1>
        """ | sudo tee /var/www/html/index.html

        echo "Setup Miniconda environment"

        sudo wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
        sudo bash miniconda.sh -b -p miniconda
        sudo rm miniconda.sh
        export PATH=/miniconda/bin:$PATH > ~/.bashrc
        conda init bash
        source ~/.bashrc
        conda create -y -n pygrid python=3.7
        conda activate pygrid

        echo "Install poetry..."
        pip install poetry

        echo "Install GCC"
        sudo apt-get install python3-dev -y
        sudo apt-get install libevent-dev -y
        sudo apt-get install gcc -y

        echo "Cloning PyGrid"
        git clone https://github.com/OpenMined/PyGrid

        cd /PyGrid/apps/{self.config.app.name}
        poetry install
        nohup ./run.sh --port {self.config.app.port}  --host {self.config.app.host} {f"--id {self.config.app.id} --network {self.config.app.network}" if self.config.app.name == "node" else ""}
        '''

        with open(f"{self.root_dir}/deploy.sh", "w") as deploy_file:
            deploy_file.write(exec_script)
