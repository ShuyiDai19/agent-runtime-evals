from pydantic import BaseModel, ConfigDict

from runtime.tool_registry import Tool


class SearchLogsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str
    query: str


class SearchLogsTool(Tool):
    name = "search_logs"

    description = (
        "Search recent application logs for a service. "
        "Use the query to describe the error or behavior "
        "you want to investigate."
    )

    args_schema = SearchLogsArgs

    _logs = {
        "payments-api": [
            {
                "timestamp": "2026-09-29T21:43:11Z",
                "level": "ERROR",
                "message": (
                    "PaymentMetadataValidationError: "
                    "field 'merchant_context' missing"
                ),
            },
            {
                "timestamp": "2026-09-29T21:43:14Z",
                "level": "ERROR",
                "message": (
                    "Failed to deserialize legacy payment "
                    "metadata payload"
                ),
            },
            {
                "timestamp": "2026-09-29T21:44:02Z",
                "level": "WARN",
                "message": (
                    "Request failure rate exceeded "
                    "10 percent threshold"
                ),
            },
        ],
        "checkout-api": [
            {
                "timestamp": "2026-09-29T21:44:10Z",
                "level": "INFO",
                "message": (
                    "Checkout request completed successfully"
                ),
            }
        ],
        "auth-api": [
            {
                "timestamp": "2026-09-29T21:44:18Z",
                "level": "INFO",
                "message": (
                    "Authentication request completed"
                ),
            }
        ],
        "inventory-api": [
            {
                "timestamp": "2026-09-29T20:18:21Z",
                "level": "ERROR",
                "message": (
                    "DBPoolTimeoutError: connection "
                    "acquisition exceeded 500ms"
                ),
            },
            {
                "timestamp": "2026-09-29T20:18:27Z",
                "level": "ERROR",
                "message": (
                    "Database connection pool exhausted"
                ),
            },
            {
                "timestamp": "2026-09-29T20:19:04Z",
                "level": "WARN",
                "message": (
                    "Inventory request latency exceeded "
                    "600ms threshold"
                ),
            },
        ],
    }

    def execute(
        self,
        service: str,
        query: str,
    ) -> dict:
        return {
            "service": service,
            "query": query,
            "matches": self._logs.get(
                service,
                [],
            ),
        }