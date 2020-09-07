output "pygrid-network-websocket-connection-endpoint" {
  description = "Websocket connection endpoint"
  value       = aws_apigatewayv2_stage.Test.invoke_url
}