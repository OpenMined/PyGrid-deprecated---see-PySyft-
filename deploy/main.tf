# Configure the AWS Provider
provider "aws" {
  version                 = "~> 2.0"
  region                  = var.aws_region
  shared_credentials_file = "$HOME/.aws/credentials"
}


# Create Virtual Private Cloud (VPC)
resource "aws_vpc" "main" {
  cidr_block       = "10.0.0.0/16" #TODO: Move it to variables.tf
  instance_tenancy = "default"

  tags = {
    Name = "main-vpc"
  }
}

# Create Internet Gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-gw"
  }
}

# Create Route Table
resource "aws_route_table" "route-table" {
  vpc_id = aws_vpc.main.id

  route { # Default Route to GW
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  route {
    ipv6_cidr_block = "::/0"
    gateway_id      = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "main-route-table"
  }
}

# Create subnet for webservers
resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24" #TODO: Move it to variables.tf

  tags = {
    Name = "main-subnet"
  }
}

# Associate subnet with the route table
resource "aws_route_table_association" "rta" {
  subnet_id      = aws_subnet.main.id
  route_table_id = aws_route_table.route-table.id
}

# Create security group
resource "aws_security_group" "web" {
  name        = "allow_web_traffic"
  description = "Allow web inbound traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "allow_web"
  }
}

# Create network interface
resource "aws_network_interface" "webserver" {
  subnet_id       = aws_subnet.main.id
  private_ips     = ["10.0.1.50"]
  security_groups = ["${aws_security_group.web.id}"]
}


# Assign elastic IP to the network interface
resource "aws_eip" "one" {
  vpc                       = true
  network_interface         = aws_network_interface.webserver.id
  associate_with_private_ip = "10.0.1.50"
  depends_on                = [aws_internet_gateway.gw]
}

resource "aws_instance" "webserver-instance" {
  ami           = var.amis[var.aws_region]
  instance_type = "t2.micro"
  # key_name      = "openmined_pygrid"

  network_interface {
    device_index         = 0
    network_interface_id = aws_network_interface.webserver.id
  }

  user_data = file("deploy.sh")

  tags = {
    Name = "OpenMinedWebServer"
  }
}


output "server_public_ip" {
  value = aws_eip.one.public_ip
}
