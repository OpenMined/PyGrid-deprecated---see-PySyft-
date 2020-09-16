resource "aws_efs_file_system" "pygrid-syft-dependenices" {
  creation_token   = "pygrid-syft-dependencies"

  encrypted        = true
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  lifecycle_policy {
    transition_to_ia = "AFTER_90_DAYS"
  }

  tags = {
    Name = "pygrid-syft-dependencies"
  }
}

resource "aws_efs_access_point" "node-access-points" {
  file_system_id = aws_efs_file_system.pygrid-syft-dependenices.id

  root_directory {
    path = "/dep"
  }

  tags = {
    Name = "node-efs-access-point"
  }
}

# Note: Creates mount target in each subnet in the region
resource "aws_efs_mount_target" "node-efs-mount-targets" {
  file_system_id = aws_efs_file_system.pygrid-syft-dependenices.id
  for_each       = data.aws_subnet_ids.all.ids
  subnet_id      = each.value
}


resource "aws_security_group" "allow_efs" {
  name        = "node_efs_allow_lambda"
  description = "Allow inbound traffic"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "NFS from VPC"
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
    Name = "node_efs_allow_lambda"
  }
}