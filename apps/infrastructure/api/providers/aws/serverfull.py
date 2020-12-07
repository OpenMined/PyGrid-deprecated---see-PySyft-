from ...tf import var
from .aws import *


class AWS_Serverfull(AWS):
    def __init__(self, config) -> None:
        """
        credentials (dict) : Contains AWS credentials
        """

        super().__init__(config)

        self.writing_exec_script()

        self.build_security_group()
        self.build_instance()
        self.build_load_balancer()
        self.build_database()
        self.output()

    def output(self):
        self.tfscript += terrascript.Output(
            "instance_endpoint",
            value=var_module(self.instances, "public_ip"),
            description="The public IP address of the main server instance.",
        )

    def build_security_group(self):
        # ----- Security Group ------#

        self.security_group = resource.aws_security_group(
            "security_group",
            name=f"pygrid-{self.config.app.name}-security-group",
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
            instance_count=self.config.app.count,
            source="terraform-aws-modules/ec2-instance/aws",
            name=f"pygrid-{self.config.app.name}-instances",
            ami=var(self.ami.id),
            instance_type=self.config.vpc.instance_type,
            associate_public_ip_address=True,
            monitoring=True,
            vpc_security_group_ids=[var(self.security_group.id)],
            subnet_ids=[var(public_subnet.id) for _, public_subnet in self.subnets],
            user_data=var(f'file("{self.root_dir}/deploy.sh")'),
            tags={"Name": f"pygrid-{self.config.app.name}-instances"},
        )
        self.tfscript += self.instances

    def build_load_balancer(self):
        self.load_balancer = Module(
            "pygrid_load_balancer",
            source="terraform-aws-modules/elb/aws",
            name=f"pygrid-{self.config.app.name}-load-balancer",
            subnets=[var(public_subnet.id) for _, public_subnet in self.subnets],
            security_groups=[var(self.security_group.id)],
            number_of_instances=self.config.app.count,
            instances=[
                var_module(self.instances, f"id[{i}]")
                for i in range(self.config.app.count)
            ],
            listener=[
                {
                    "instance_port": "80",
                    "instance_protocol": "HTTP",
                    "lb_port": "80",
                    "lb_protocol": "HTTP",
                },
                {
                    "instance_port": "8080",
                    "instance_protocol": "http",
                    "lb_port": "8080",
                    "lb_protocol": "http",
                },
            ],
            health_check={
                "target": "HTTP:80/",
                "interval": 30,
                "healthy_threshold": 2,
                "unhealthy_threshold": 2,
                "timeout": 5,
            },
            tags={"Name": f"pygrid-{self.config.app.name}-load-balancer"},
        )
        self.tfscript += self.load_balancer

    def build_database(self):
        """Builds a MySQL central database."""

        db_subnet_group = resource.aws_db_subnet_group(
            "default",
            name=f"{self.config.app.name}-db-subnet-group",
            subnet_ids=[var(private_subnet.id) for private_subnet, _ in self.subnets],
            tags={"Name": f"pygrid-{self.config.app.name}-db-subnet-group"},
        )
        self.tfscript += db_subnet_group

        self.database = resource.aws_db_instance(
            f"pygrid-{self.config.app.name}-database",
            engine="mysql",
            port="3306",
            name="pygridDB",
            instance_class="db.t2.micro",
            storage_type="gp2",  # general purpose SSD
            identifier=f"pygrid-{self.config.app.name}-db",  # name
            username=self.config.credentials.db.username,
            password=self.config.credentials.db.password,
            db_subnet_group_name=var(db_subnet_group.id),
            apply_immediately=True,
            skip_final_snapshot=True,
            # Storage Autoscaling
            allocated_storage=20,
            max_allocated_storage=100,
            tags={"Name": f"pygrid-{self.config.app.name}-aurora-database"},
        )
        self.tfscript += self.database

    def writing_exec_script(self):
        exec_script = f'''
        #cloud-boothook
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
