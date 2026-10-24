from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class TestRequest(BaseModel):
    url: HttpUrl
    objective: str = Field(min_length=5, max_length=500)

    # Optional extras used by the Visual Auditor (Akanksha's module).
    # CSS selectors that MUST exist and be visible on the target page.
    expected_selectors: list[str] = Field(default_factory=list, max_length=20)
    # Re-save the current page as the visual-regression baseline.
    reset_baseline: bool = False


class TestStep(BaseModel):
    action: Literal["navigate", "click", "fill", "verify"]
    target: str
    expected: str
    value: str | None = None


class TestPlan(BaseModel):
    steps: list[TestStep] = Field(min_length=1, max_length=10)


class TestCreated(BaseModel):
    run_id: str
    status: Literal["queued", "running", "completed", "error"]
    message: str


class StepResult(BaseModel):
    name: str
    status: Literal["passed", "failed", "inconclusive"]
    message: str
    # Extra evidence for the UI (all optional, so older code keeps working).
    action: str | None = None
    target: str | None = None
    expected: str | None = None
    screenshot_url: str | None = None


class TestReport(BaseModel):
    run_id: str
    status: Literal["queued", "running", "completed", "error"]
    objective: str
    steps: list[StepResult] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    # Filled in by the orchestrator once the Visual Auditor has finished.
    visual_audit: dict | None = None
    summary: dict = Field(default_factory=dict)
