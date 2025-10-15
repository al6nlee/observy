import logging
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.trace import SpanKind


class OTelClient:
    """
    OpenTelemetry 客户端封装
    用于在 Python HTTP 服务（FastAPI/Flask）中快速启用 OTel 追踪和指标上报
    """

    def __init__(
            self,
            service_name: str,
            endpoint: str = "http://localhost:4318",
            enable_metrics: bool = False,
            fail_fast: bool = True,
    ):
        """
        初始化配置（不执行连接）
        :param service_name: 服务名，用于 trace 和 metrics 的资源标识
        :param endpoint: OTLP 导出地址（通常是 otel-collector）
        :param enable_metrics: 是否启用指标上报
        :param fail_fast: 如果 endpoint 不可达，是否直接抛出异常
        """
        self.service_name = service_name
        self.endpoint = endpoint.rstrip("/")
        self.enable_metrics = enable_metrics
        self.fail_fast = fail_fast

        self._tracer: Optional[trace.Tracer] = None
        self._meter: Optional[metrics.Meter] = None
        self._initialized = False

    # -------------------------
    # 公共 API
    # -------------------------
    def init(self):
        """初始化 Tracer / Metrics 并检测 OTLP collector 可用性"""
        if self._initialized:
            logging.debug("[otel] already initialized, skipping reinit")
            return

        resource = Resource.create({"service.name": self.service_name})

        # --- Tracer ---
        trace_provider = TracerProvider(resource=resource)
        trace_exporter = OTLPSpanExporter(endpoint=f"{self.endpoint}/v1/traces")
        trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(trace_provider)
        self._tracer = trace.get_tracer(self.service_name)

        # --- Metrics（可选） ---
        if self.enable_metrics:
            metric_exporter = OTLPMetricExporter(endpoint=f"{self.endpoint}/v1/metrics")
            metric_reader = PeriodicExportingMetricReader(metric_exporter)
            meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
            metrics.set_meter_provider(meter_provider)
            self._meter = metrics.get_meter(self.service_name)

        self._initialized = True
        logging.info(f"[otel] initialized for service='{self.service_name}' -> {self.endpoint}")

    # -------------------------
    # 框架注入
    # -------------------------
    def instrument_fastapi(self, app):
        """为 FastAPI 应用注入 OTel 中间件"""
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logging.info("[otel] FastAPI instrumentation enabled")

    def instrument_flask(self, app):
        """为 Flask 应用注入 OTel 中间件"""
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        FlaskInstrumentor().instrument_app(app)
        logging.info("[otel] Flask instrumentation enabled")

    # -------------------------
    # 属性访问
    # -------------------------
    @property
    def tracer(self) -> trace.Tracer:
        if not self._tracer:
            self._tracer = trace.get_tracer(self.service_name)
        return self._tracer

    @property
    def meter(self) -> metrics.Meter:
        if not self._meter:
            self._meter = metrics.get_meter(self.service_name)
        return self._meter
