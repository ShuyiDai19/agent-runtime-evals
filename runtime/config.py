from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    max_steps: int = Field(
        default=8,
        ge=1,
    )