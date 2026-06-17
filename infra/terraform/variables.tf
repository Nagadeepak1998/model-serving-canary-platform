variable "namespace" {
  description = "Kubernetes namespace for the canary platform."
  type        = string
  default     = "ml-platform"
}

variable "image" {
  description = "Container image to deploy."
  type        = string
}

variable "default_canary_percent" {
  description = "Default canary traffic percentage."
  type        = number
  default     = 25
}
