from pydantic import BaseModel

from runtime.tool_registry import Tool


class GetServiceStatusArgs(BaseModel):
    service: str


class GetServiceStatusTool(Tool):
    name = "get_service_status"

    description = (
        "Get the current operational status of a service."
    )

    args_schema = GetServiceStatusArgs

    _service_data = {
        "payments-api": {
            "status": "degraded",
            "error_rate": 0.127,
            "latency_ms": 842,
        },
        "checkout-api": {
            "status": "healthy",
            "error_rate": 0.008,
            "latency_ms": 214,
        },
        "auth-api": {
            "status": "healthy",
            "error_rate": 0.004,
            "latency_ms": 98,
        },
    }

    def execute(self, service: str) -> dict:
        if service not in self._service_data:
            return {
                "service": service,
                "status": "unknown",
            }

        return {
            "service": service,
            **self._service_data[service],
        }