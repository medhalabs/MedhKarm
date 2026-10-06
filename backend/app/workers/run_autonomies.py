"""Gives the build graph the founder's autonomy settings (features/autonomy) for the company
whose run is going, without the workflows feature knowing about them."""

from app.core.tenant import current_company
from app.features.autonomy.service import AutonomyService
from app.features.workflows.schemas import RunAutonomy


class RunAutonomies:
    def __init__(self, autonomy: AutonomyService) -> None:
        self._autonomy = autonomy

    async def for_run(self, run_id: str) -> RunAutonomy | None:
        company = current_company.get()
        if company is None:  # no company (evals): the template's rules
            return None
        policy, go_live = await self._autonomy.for_run(company, run_id)
        return RunAutonomy(policy=policy, go_live=go_live)
