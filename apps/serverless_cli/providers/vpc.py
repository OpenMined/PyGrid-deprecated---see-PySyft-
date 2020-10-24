import terrascript.resource as resource
import math

var = lambda x: "${" + x + "}"
var_module = lambda x, y: var(f"module.{x._name}.{y}")


def generate_cidr_block(num_ip_addresses, num_subnets):
    cidr_block_step = int(num_ip_addresses / num_subnets)
    subnet_ip_prefix = 32 - int(math.log(cidr_block_step, 2))
    for i in range(num_subnets):
        yield f"10.0.0.{cidr_block_step * i}/{subnet_ip_prefix}"


def deploy_vpc(tfscript, app, av_zones):
    """
    app (str) : The app("node"/"network") which is to be deployed.
    av_zones (list) : List of availability zones in the region in which VPC subnets should be created.
    """

    # ----- Virtual Private Cloud (VPC) ------#

    vpc = resource.aws_vpc(
        f"pygrid-{app}",
        cidr_block="10.0.0.0/26",  # 2**(32-26) = 64 IP Addresses
        instance_tenancy="default",
        enable_dns_hostnames=True,
        tags={"Name": f"pygrid-{app}-vpc"},
    )
    tfscript += vpc

    # ----- Internet Gateway -----#

    internet_gateway = resource.aws_internet_gateway(
        "igw", vpc_id=var(vpc.id), tags={"Name": f"pygrid-{app}-igw"}
    )
    tfscript += internet_gateway

    # ----- Route Tables -----#

    # One public route table for all public subnets across different availability zones
    # public_rt = resource.aws_route_table(
    #     "public-RT",
    #     vpc_id=var(vpc.id),
    #     route=[
    #         {
    #             "cidr_block": "0.0.0.0/0",
    #             "ipv6_cidr_block": "::/0",
    #             "gateway_id": var(internet_gateway.id),
    #             "egress_only_gateway_id": "",
    #             "instance_id": "",
    #             "local_gateway_id": "",
    #             "nat_gateway_id": "",
    #             "network_interface_id": "",
    #             "transit_gateway_id": "",
    #             "vpc_peering_connection_id": "",
    #         }
    #     ],
    #     tags={"Name": f"pygrid-{app}-public-RT"},
    # )
    # tfscript += public_rt

    # ----- Subnets ----- #

    num_ip_addresses = 2 ** (32 - 26)
    num_subnets = 2 * len(
        av_zones
    )  # Each Availability zone contains one public and one private subnet

    cidr_blocks = generate_cidr_block(num_ip_addresses, num_subnets)
    subnets = []

    for i, av_zone in enumerate(av_zones):

        """
        Each availability zone contains
         - one public subnet : Connects to the internet via public route table
         - one private subnet : Hosts the lambda function
         - one NAT gateway (in the public subnet) : Allows traffic from the internet to the private subnet
            via the public subnet
         - one Route table : Routes the traffic from the NAT gateway to the private subnet
        """

        private_subnet = resource.aws_subnet(
            f"private-subnet-{i}",
            vpc_id=var(vpc.id),
            cidr_block=next(cidr_blocks),
            availability_zone=av_zone,
            tags={"Name": f"{app}-private-{i}"},
        )
        tfscript += private_subnet

        public_subnet = resource.aws_subnet(
            f"public-subnet-{i}",
            vpc_id=var(vpc.id),
            cidr_block=next(cidr_blocks),
            availability_zone=av_zone,
            tags={"Name": f"{app}-public-{i}"},
        )
        tfscript += public_subnet

        subnets.append((private_subnet, public_subnet))

        # Elastic IP for NAT Gateway
        elastic_ip = resource.aws_eip(
            f"eip-{i}", vpc=True, tags={"Name": f"pygrid-{app}-EIP-{i}"}
        )
        tfscript += elastic_ip

        # NAT Gateway
        nat_gateway = resource.aws_nat_gateway(
            f"ngw-{i}",
            allocation_id=var(elastic_ip.id),
            subnet_id=var(public_subnet.id),
            tags={"Name": f"pygrid-{app}-ngw-{i}"},
        )
        tfscript += nat_gateway

        # Route table for private subnet
        # private_rt = resource.aws_route_table(
        #     f"private-RT-{i}",
        #     vpc_id=var(vpc.id),
        #     route=[
        #         {
        #             "cidr_block": "0.0.0.0/0",
        #             "ipv6_cidr_block": "::/0",
        #             "gateway_id": "",
        #             "egress_only_gateway_id": "",
        #             "instance_id": "",
        #             "local_gateway_id": "",
        #             "nat_gateway_id": var(nat_gateway.id),
        #             "network_interface_id": "",
        #             "transit_gateway_id": "",
        #             "vpc_peering_connection_id": "",
        #         }
        #     ],
        #     tags={"Name": f"pygrid-{app}-private-RT-{i}"},
        # )
        # tfscript += private_rt

        # Associate public subnet with public route table
        # tfscript += resource.aws_route_table_association(
        #     f"rta-public-subnet-{i}",
        #     subnet_id=var(public_subnet.id),
        #     route_table_id=var(public_rt.id),
        # )
        #
        # # Associate private subnet with private route table
        # tfscript += resource.aws_route_table_association(
        #     f"rta-private-subnet-{i}",
        #     subnet_id=var(private_subnet.id),
        #     route_table_id=var(private_rt.id),
        # )

    return tfscript, vpc, subnets
