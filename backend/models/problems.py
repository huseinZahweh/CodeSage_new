from pydantic import BaseModel, Field
from typing import Literal

class Submission(BaseModel):
    problem_id: int = Field(..., example=1)
    code: str = Field(..., min_length=1, example="print('Hello')")
    verdict: Literal["Accepted", "Rejected", "Pending", "None"] = Field(
        default="Pending",
        description="Verdict can be Accepted, Rejected, Pending, or None"
    )