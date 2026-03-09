from pydantic import BaseModel
from typing import Any, Optional


class StatusResponse(BaseModel):
    session_id: str
    current_stage: Optional[str]
    stage_status: dict[str, str]
    confirmed_outputs: dict[str, Any]


class UploadResponse(BaseModel):
    filename: str
    rows: int
    columns: int
    column_info: list[dict[str, Any]]


class TargetRequest(BaseModel):
    target: str


class ColumnDecision(BaseModel):
    column: str
    decision: str  # "keep", "drop", or ""
    note: str = ""


# Confirm payloads
class ETLConfirm(BaseModel):
    target: str
    columns: list[ColumnDecision]


class StatsConfirm(BaseModel):
    selected_features: list[str]


class ModelConfirm(BaseModel):
    model_type: str = "RandomForest"
    hyperparameters: dict[str, Any] = {}


class EvaluateConfirm(BaseModel):
    threshold: float = 0.5
    primary_metric: str = "recall"


