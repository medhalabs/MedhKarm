from pydantic import BaseModel, Field, model_validator

from app.features.approvals.schemas import ApprovalPolicy


class RoleSpec(BaseModel):
    """One seat on a team: what it does, how it behaves, what it may touch."""

    id: str = Field(pattern=r"^[a-z][a-z_]*$")  # also the actor name in the activity log
    title: str
    display_names: list[str] = Field(min_length=1)  # names shown in the office, in order
    responsibilities: str  # one line for the founder
    instructions: str = ""  # the agent's system prompt; empty for roles that don't use a model
    review_instructions: str = ""  # for roles that review others' work (the CTO)
    tools: list[str] = Field(default_factory=list)
    model: str | None = None  # LiteLLM model name; None = the default model
    max_steps: int | None = Field(default=None, ge=1, le=200)
    count: int = Field(default=1, ge=1)  # how many the team starts with
    max_count: int = Field(default=1, ge=1)  # how many the CTO may add
    active: bool = True  # False = defined, not yet part of the workflow

    @model_validator(mode="after")
    def _count_within_max(self) -> "RoleSpec":
        if self.count > self.max_count:
            raise ValueError(f"role {self.id}: count {self.count} exceeds max_count")
        return self


class TeamTemplate(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z_-]*$")
    name: str
    description: str
    workflow: str
    checker: str
    roles: list[RoleSpec] = Field(min_length=1)
    approval: ApprovalPolicy = Field(default_factory=ApprovalPolicy)  # rules at the gates

    def role(self, role_id: str) -> RoleSpec:
        for role in self.roles:
            if role.id == role_id:
                return role
        raise KeyError(role_id)


class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str
    roles: list[str]  # titles of active roles


class TeamMember(BaseModel):
    """One agent on an assembled team."""

    role: str
    title: str
    name: str


class Team(BaseModel):
    template_id: str
    members: list[TeamMember]
