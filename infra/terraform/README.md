# Terraform Notes

This skeleton mirrors the Kubernetes manifests for a simple cluster deployment.

## Intended use

- Set `image` to a published container reference.
- Point the Kubernetes provider at a reachable cluster.
- Run `terraform init` and `terraform apply`.

It is deliberately small and keeps rollout control inside the application rather than trying to automate progressive delivery with a service mesh.
