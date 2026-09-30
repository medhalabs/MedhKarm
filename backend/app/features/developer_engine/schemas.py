from pydantic import BaseModel, Field


class DevTask(BaseModel):
    description: str
    test_command: str = Field(description="Shell command, run in the workspace, that must exit 0")


class DevResult(BaseModel):
    success: bool
    summary: str
    files_changed: list[str] = Field(default_factory=list)
    test_output: str = ""
    steps: int = 0
    total_tokens: int = 0
