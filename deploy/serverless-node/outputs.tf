output "this_apigatewayv2_api_api_endpoint" {
  description = "My Blogs awesome API endpoint"
  value       = module.api_gateway.this_apigatewayv2_api_api_endpoint
}

//output "this_subnet_ip" {
//  description = "Subnet Id"
//  value       = aws_efs_mount_target.alpha.subnet_id
//}