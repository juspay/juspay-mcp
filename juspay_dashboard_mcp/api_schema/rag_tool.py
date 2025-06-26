from pydantic import BaseModel, Field
from typing import Optional


class JuspayRagQueryPayload(BaseModel):
    """
    Payload schema for RAG query tool.
    """

    query: str = Field(
        ..., description="The question to ask the RAG system", min_length=1
    )
    similarity_top_k: Optional[int] = Field(
        default=20, description="Number of similar documents to retrieve", ge=1, le=100
    )
    include_metrics: Optional[bool] = Field(
        default=True, description="Whether to include performance metrics in response"
    )
