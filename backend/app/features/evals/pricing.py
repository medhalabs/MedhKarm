"""Money per eval task: what it cost on the model it ran on, and what the same tokens would
cost on reference models (evals/prices.toml). Prompt-caching discounts aren't applied, so
paid-model figures are an upper estimate for the same token counts."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


class ModelPrice(BaseModel):
    id: str
    label: str
    input_usd: float  # per million tokens
    output_usd: float
    reference: bool = False

    def cost_usd(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (prompt_tokens * self.input_usd + completion_tokens * self.output_usd) / 1e6


class PriceTable(BaseModel):
    usd_to_inr: float = 88.0
    models: list[ModelPrice] = Field(default_factory=list)

    @property
    def references(self) -> list[ModelPrice]:
        return [m for m in self.models if m.reference]

    def find(self, model_id: str) -> ModelPrice | None:
        """By exact id, or by the part after a LiteLLM provider prefix ("anthropic/claude-…")."""
        for model in self.models:
            if model.id == model_id or model_id.split("/", 1)[-1] == model.id:
                return model
        return None


def load_prices(path: Path) -> PriceTable:
    if not path.exists():
        return PriceTable()
    return PriceTable.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
