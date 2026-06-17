output "namespace" {
  value = kubernetes_namespace.platform.metadata[0].name
}

output "deployment_name" {
  value = kubernetes_deployment.api.metadata[0].name
}
