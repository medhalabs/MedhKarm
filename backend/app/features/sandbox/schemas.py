from pydantic import BaseModel


class CommandResult(BaseModel):
    exit_code: int
    output: str  # stdout and stderr combined, in order

    @property
    def ok(self) -> bool:
        return self.exit_code == 0
