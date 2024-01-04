from __future__ import annotations

import pydantic
from pydantic import BaseModel, Field

PYDANTIC_VERSION = tuple(pydantic.VERSION.split('.'))


class TextPoint(BaseModel):
    line: int
    character: int


class TextRange(BaseModel):
    start: TextPoint
    end: TextPoint


class LintOrigin(BaseModel):
    line: int
    column: int
    absolute_location: str


class LintResult(BaseModel):
    message: str
    range: TextRange
    path: str
    rule_id: str = Field(alias='ruleId')
    rule_severity: str = Field(alias='ruleSeverity')
    origin: LintOrigin | None = None


if PYDANTIC_VERSION < ('2',):
    def parse_result(raw_result: dict) -> LintResult:
        return LintResult.parse_obj(raw_result)
else:
    def parse_result(raw_result: dict) -> LintResult:
        return LintResult.model_validate(raw_result)
