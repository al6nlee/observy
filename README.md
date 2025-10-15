# observy

Project Name: Observy

Description:
Observy is a lightweight Python module that seamlessly integrates OpenTelemetry (OTel) into HTTP services. It provides automatic tracing, metrics collection, and observability enhancements with minimal configuration, enabling developers to gain deeper insights into service performance and reliability.

Key Features:

Easy integration with any Python HTTP service (Flask, FastAPI, Django, etc.)

Automatic tracing for incoming HTTP requests

Metrics collection compatible with Prometheus and other observability tools

Minimal setup, designed for reuse across multiple projects

Extensible for custom instrumentation

Use Case:
Ideal for teams that want to improve observability and monitor HTTP services without rewriting existing code or introducing complex instrumentation logic.

# how to use

```python
from fastapi import FastAPI
from observy.otel import OTelClient

app = FastAPI()

otel = OTelClient(
    service_name="example-fastapi",
    endpoint="http://localhost:4318",
    enable_metrics=False,
)
otel.init()
otel.instrument_fastapi(app)


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/compute")
def compute(x: int, y: int):
    with otel.tracer.start_as_current_span("compute_sum") as span:
        result = x + y
        span.set_attribute("input.x", x)
        span.set_attribute("input.y", y)
        span.set_attribute("output.result", result)
        return {"result": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
```