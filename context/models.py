from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApplicationContext(BaseModel):
    """
    Shared application context for a VAPT project.

    This is the project-level source of truth that AI Skills,
    RAG retrieval and testers can consume later.
    """

    model_config = ConfigDict(extra="forbid")

    project_id: str
    target: str

    scope: List[str] = Field(default_factory=list)

    technologies: List[str] = Field(default_factory=list)

    authentication: Dict[str, Any] = Field(default_factory=dict)

    roles: List[str] = Field(default_factory=list)

    assets: List[str] = Field(default_factory=list)

    notes: Optional[str] = None

    version: int = 1