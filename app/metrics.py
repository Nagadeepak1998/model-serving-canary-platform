from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response


prediction_requests_total = Counter(
    "prediction_requests_total",
    "Count of prediction requests by selected model.",
    ["selected_model"],
)

shadow_priority_mismatch_total = Counter(
    "shadow_priority_mismatch_total",
    "Count of priority mismatches between baseline and canary predictions.",
)

prediction_latency_seconds = Histogram(
    "prediction_latency_seconds",
    "Latency for prediction requests.",
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")
