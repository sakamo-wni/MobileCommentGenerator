"""Unified API response types for type safety"""

from typing import TypeVar, Generic, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Import types only when needed to avoid circular imports

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class ApiError(BaseModel):
    """Structured error response"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Specific response data models
class CommentGenerationData(BaseModel):
    """Data for comment generation response"""
    location: str
    comment: Optional[str] = None
    advice_comment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Change to Dict to accept any metadata format

class LocationData(BaseModel):
    """Data for location response"""
    locations: list[str]

class HistoryData(BaseModel):
    """Data for history response"""
    history: list[Dict[str, Any]]  # Using Dict for flexibility with history items

class ProviderData(BaseModel):
    """Data for provider information"""
    id: str
    name: str
    description: str

class ProvidersData(BaseModel):
    """Data for providers response"""
    providers: list[ProviderData]

# Type aliases for specific responses
CommentGenerationResponse = ApiResponse[CommentGenerationData]
LocationResponse = ApiResponse[LocationData]
HistoryResponse = ApiResponse[HistoryData]
ProvidersResponse = ApiResponse[ProvidersData]