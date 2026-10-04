from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    max_steps: int = Field(
        default=8,
        ge=1,
    )

    max_tool_retries: int = Field(
        default=2,
        ge=0,
    )

    retry_backoff_seconds: float = Field(
        default=0.25,
        ge=0.0,
    )