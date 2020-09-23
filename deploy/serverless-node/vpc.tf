# Create Virtual Private Cloud (VPC)
resource "aws_vpc" "pygrid_node" {
  cidr_block           = "10.0.0.0/26"
  instance_tenancy     = "default"
  enable_dns_hostnames = true

  tags = {
    Name = "pygrid-node-vpc"
  }
}


# --Create private subnets for lambda-- #

# Availability zone "us-east-1a"
resource "aws_subnet" "private_subnet_1" {
  vpc_id            = aws_vpc.pygrid_node.id
  cidr_block        = "10.0.0.0/28"
  availability_zone = "us-east-1a"
  tags = {
    Name = "Pygrid-Node-Private-Subnet-1"
  }
}

# Availability zone "us-east-1b"
resource "aws_subnet" "private_subnet_2" {
  vpc_id            = aws_vpc.pygrid_node.id
  cidr_block        = "10.0.0.16/28"
  availability_zone = "us-east-1b"
  tags = {
    Name = "Pygrid-Node-Private-Subnet-2"
  }
}

# Create public subnet
resource "aws_subnet" "public_subnet" {
  vpc_id     = aws_vpc.pygrid_node.id
  cidr_block = "10.0.0.32/28"

  tags = {
    Name = "Pygrid-Node-Public-Subnet"
  }
}

# Create Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.pygrid_node.id

  tags = {
    Name = "pygrid-node-igw"
  }
}



# Create EIP for NAT Gateway
resource "aws_eip" "eip" {
  vpc = true
}


# Create NAT Gateway
resource "aws_nat_gateway" "ngw" {
  allocation_id = aws_eip.eip.id
  subnet_id     = aws_subnet.public_subnet.id

  tags = {
    Name = "pygrid-node-ngw"
  }
}


# Create Route Table for Public Subnet
resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.pygrid_node.id

  route {
    # Route to Internet GW
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "pygrid-node-public-RT"
  }
}

# Create Route Table for Private Subnet
resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.pygrid_node.id
  
  route {
    # Route to NAT GW
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_nat_gateway.ngw.id
  }

  tags = {
    Name = "pygrid-node-private-RT"
  }
}

# Associate subnet with the route table
resource "aws_route_table_association" "rta_public_subnet" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "rta_private_subnet_1" {
  subnet_id      = aws_subnet.private_subnet_1.id
  route_table_id = aws_route_table.private_route_table.id
}

resource "aws_route_table_association" "rta_private_subnet_2" {
  subnet_id      = aws_subnet.private_subnet_2.id
  route_table_id = aws_route_table.private_route_table.id
}
