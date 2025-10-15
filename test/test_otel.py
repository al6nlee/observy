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
