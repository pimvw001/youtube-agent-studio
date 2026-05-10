from typing import Literal

from pydantic import BaseModel, Field

ReviewDecision = Literal["approved", "needs_more_research", "needs_script_changes"]


class ReviewResult(BaseModel):
    """Structured output van de ReviewAgent.

    Dit maakt de agnetic loop minder fragiel dan alleen vrije tekst.
    De LLM kan alsnog rommelige output geven, daarom staat de fallback-parser   
    """

    decision: ReviewDecision = "approved"
    score: int = Field(default=7, ge=1, le=10)
    feedback: list[str] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)


class ReviewIteration(BaseModel):
    round_number: int
    decision: ReviewDecision
    score: int
    feedback: list[str]
    action: str
