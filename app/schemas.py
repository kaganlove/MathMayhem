"""Pydantic request and response schemas for Math Mayhem."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    token: str = Field(..., min_length=1)


class EpisodeCreateRequest(BaseModel):
    code: str = Field(..., pattern=r"^EP\d{3,4}$")
    title: str = Field(..., min_length=1, max_length=200)
    concept_summary: str = Field(default="")
    aspect_ratio: str = Field(default="9:16")


class JobCreateRequest(BaseModel):
    job_type: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)


class HealthStatusResponse(BaseModel):
    status: str
    version: str
    gpu: Dict[str, Any]
    disk_free_gb: float
    database_ok: bool
    queued_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
