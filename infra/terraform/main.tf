resource "kubernetes_namespace" "platform" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_deployment" "api" {
  metadata {
    name      = "model-serving-canary-platform"
    namespace = kubernetes_namespace.platform.metadata[0].name
    labels = {
      app = "model-serving-canary-platform"
    }
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "model-serving-canary-platform"
      }
    }

    template {
      metadata {
        labels = {
          app = "model-serving-canary-platform"
        }
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/path"   = "/metrics"
          "prometheus.io/port"   = "8000"
        }
      }

      spec {
        container {
          name  = "api"
          image = var.image

          port {
            container_port = 8000
          }

          env {
            name  = "DEFAULT_CANARY_PERCENT"
            value = tostring(var.default_canary_percent)
          }
        }
      }
    }
  }
}
