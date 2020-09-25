variable "key_name" {
  default = "ec2_efs_key"
}

# Data sources to get VPC and subnets
data "aws_vpc" "default" {
  default = true
}

data "aws_subnet_ids" "all" {
  vpc_id = data.aws_vpc.default.id
}

resource "aws_security_group" "ec2_sg" {
  name        = "ec2_efs_sg"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allows to mount EFS"
    from_port   = 2049
    to_port     = 2049
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
    Name = "ec2_efs_sg"
  }
}

resource "aws_key_pair" "default" {
  key_name   = var.key_name
  public_key = file("${var.key_name}.pub")
}

resource "aws_instance" "ec2_mount_efs" {

  # TODO: future proof ami attribute
  # AWS can change ami names, so we need to make our ami attribute dynamic
  ami           = "ami-0dba2cb6798deb6d8" # us-east-1  # ubuntu
  instance_type = "t2.large"
  key_name      = aws_key_pair.default.key_name

  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]

  tags = {
    Name = "ec2-mount-efs"
  }

  # Connects to remote instance and executes commands inside provisioner block
  connection {
    type        = "ssh"
    user        = "ubuntu"
    host        = self.public_ip
    private_key = file(var.key_name)
    timeout     = "2m"
  }

  # Executes only once, when the server is provisioned
  provisioner "remote-exec" {
    inline = [
      "echo \"export EFS_DNS=${aws_efs_file_system.pygrid-syft-dependenices.dns_name}\" >> ~/.bashrc",
      # file("deploy.sh")
    ]
  }

  user_data = <<-EOF
              #!/bin/bash
              echo 'Mount EFS to ~/efs'
              mkdir -p ~/efs
              sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $EFS_DNS:/ ~/efs
              EOF
}