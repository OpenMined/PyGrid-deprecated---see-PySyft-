output "this_apigatewayv2_api_api_endpoint" {
  description = "PyGrid Node API endpoint"
  value       = module.api_gateway.this_apigatewayv2_api_api_endpoint
}

output "efs-dns-name" {
  description = "Use this output DNS name to install Syft via EC2"
  value = aws_efs_file_system.pygrid-syft-dependenices.dns_name
}