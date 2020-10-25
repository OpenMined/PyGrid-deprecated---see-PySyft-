from ..utils import generate_cidr_block
from ..provider import *
from ...tf import TF, var, var_module


class AWS(Provider):
    """Amazon Web Services (AWS) Cloud Provider."""

    def __init__(self, region, av_zones, credentials, db_username, db_password) -> None:
        """
        db_username (str): Username of the database about to be deployed
        db_password (str): Username of the database about to be deployed
        """
        super().__init__()

        self.region = region
        self.av_zones = av_zones
        self.credentials = credentials

        self.tfscript += terrascript.provider.aws(
            region=self.region, shared_credentials_file=self.credentials
        )

        self.update_script()

        # Build the VPC
        self.vpc = None
        self.subnets = []
        self.build_vpc()

        # Build the database
        self.db_username = db_username
        self.db_password = db_password
        self.build_database()

        # Initialize terraform
        TF.init()

    # TODO: ask amr if this vpc works for serverfull as well
    # if it does, then we can keep it here
    # Otherwise, we can make it an abstract method
    # and allow the child classes to implement it.

    def build_vpc(self) -> bool:
        """
        av_zones (list) : List of availability zones in the region in which VPC subnets should be created.
        """

        # ----- Virtual Private Cloud (VPC) ------#

        self.vpc = resource.aws_vpc(
            f"pygrid-vpc",
            cidr_block="10.0.0.0/26",  # 2**(32-26) = 64 IP Addresses
            instance_tenancy="default",
            enable_dns_hostnames=True,
            tags={"Name": f"pygrid-vpc"},
        )
        self.tfscript += self.vpc

        # ----- Internet Gateway -----#

        internet_gateway = resource.aws_internet_gateway(
            "igw", vpc_id=var(self.vpc.id), tags={"Name": f"pygrid-igw"}
        )
        self.tfscript += internet_gateway

        # ----- Route Tables -----#

        # One public route table for all public subnets across different availability zones
        public_rt = resource.aws_route_table(
            "public-RT",
            vpc_id=var(self.vpc.id),
            route=[
                {
                    "cidr_block": "0.0.0.0/0",
                    "gateway_id": var(internet_gateway.id),
                    "egress_only_gateway_id": "",
                    "ipv6_cidr_block": "",
                    "instance_id": "",
                    "local_gateway_id": "",
                    "nat_gateway_id": "",
                    "network_interface_id": "",
                    "transit_gateway_id": "",
                    "vpc_peering_connection_id": "",
                }
            ],
            tags={"Name": f"pygrid-public-RT"},
        )
        self.tfscript += public_rt

        # ----- Subnets ----- #

        num_ip_addresses = 2 ** (32 - 26)
        num_subnets = 2 * len(
            self.av_zones
        )  # Each Availability zone contains one public and one private subnet

        cidr_blocks = generate_cidr_block(num_ip_addresses, num_subnets)

        for i, av_zone in enumerate(self.av_zones):
            """
            Each availability zone contains
             - one public subnet : Connects to the internet via public route table
             - one private subnet : Hosts the deployed resources
             - one NAT gateway (in the public subnet) : Allows traffic from the internet to the private subnet
                via the public subnet
             - one Route table : Routes the traffic from the NAT gateway to the private subnet
            """

            private_subnet = resource.aws_subnet(
                f"private-subnet-{i}",
                vpc_id=var(self.vpc.id),
                cidr_block=next(cidr_blocks),
                availability_zone=av_zone,
                tags={"Name": f"private-{i}"},
            )
            self.tfscript += private_subnet

            public_subnet = resource.aws_subnet(
                f"public-subnet-{i}",
                vpc_id=var(self.vpc.id),
                cidr_block=next(cidr_blocks),
                availability_zone=av_zone,
                tags={"Name": f"public-{i}"},
            )
            self.tfscript += public_subnet

            self.subnets.append((private_subnet, public_subnet))

            # Elastic IP for NAT Gateway
            elastic_ip = resource.aws_eip(
                f"eip-{i}", vpc=True, tags={"Name": f"pygrid-EIP-{i}"}
            )
            self.tfscript += elastic_ip

            # NAT Gateway
            nat_gateway = resource.aws_nat_gateway(
                f"ngw-{i}",
                allocation_id=var(elastic_ip.id),
                subnet_id=var(public_subnet.id),
                tags={"Name": f"pygrid-ngw-{i}"},
            )
            self.tfscript += nat_gateway

            # Route table for private subnet
            private_rt = resource.aws_route_table(
                f"private-RT-{i}",
                vpc_id=var(self.vpc.id),
                route=[
                    {
                        "cidr_block": "0.0.0.0/0",
                        "nat_gateway_id": var(nat_gateway.id),
                        "ipv6_cidr_block": "",
                        "gateway_id": "",
                        "egress_only_gateway_id": "",
                        "instance_id": "",
                        "local_gateway_id": "",
                        "network_interface_id": "",
                        "transit_gateway_id": "",
                        "vpc_peering_connection_id": "",
                    }
                ],
                tags={"Name": f"pygrid-private-RT-{i}"},
            )
            self.tfscript += private_rt

            # Associate public subnet with public route table
            self.tfscript += resource.aws_route_table_association(
                f"rta-public-subnet-{i}",
                subnet_id=var(public_subnet.id),
                route_table_id=var(public_rt.id),
            )

            # Associate private subnet with private route table
            self.tfscript += resource.aws_route_table_association(
                f"rta-private-subnet-{i}",
                subnet_id=var(private_subnet.id),
                route_table_id=var(private_rt.id),
            )

        return True

    def build_database(self):
        """
        This class needs to be implemented in the child classes.
        :return:
        """
        pass
