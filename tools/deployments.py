from pydantic import BaseModel, ConfigDict

from runtime.tool_registry import Tool


class GetRecentDeploymentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str


class GetRecentDeploymentsTool(Tool):
    name = "get_recent_deployments"

    description = (
        "Get recent deployments for a service, including "
        "version, deployment time, and change summary."
    )

    args_schema = GetRecentDeploymentsArgs

    _deployment_data = {
        "payments-api": [
            {
                "version": "v2.4.1",
                "deployed_at": "2026-09-29T21:40:00Z",
                "status": "completed",
                "change_summary": (
                    "Migrated payment metadata parsing "
                    "to a stricter JSON schema."
                ),
            },
            {
                "version": "v2.4.0",
                "deployed_at": "2026-09-26T15:20:00Z",
                "status": "completed",
                "change_summary": (
                    "Added payment retry telemetry."
                ),
            },
        ],
        "checkout-api": [
            {
                "version": "v3.8.2",
                "deployed_at": "2026-09-28T18:10:00Z",
                "status": "completed",
                "change_summary": (
                    "Updated checkout metrics instrumentation."
                ),
            }
        ],
        "auth-api": [],
    }

    def execute(self, service: str) -> dict:
        return {
            "service": service,
            "deployments": self._deployment_data.get(
                service,
                [],
            ),
        }