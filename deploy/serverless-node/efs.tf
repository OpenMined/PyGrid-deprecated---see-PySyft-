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
    path = "/pygrid-dep"
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