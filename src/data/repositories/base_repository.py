"""Base repository interface."""

from abc import ABC, abstractmethod
from typing import Optional, List, Any


class BaseRepository(ABC):
    """Abstract base repository for data access."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository (create tables, etc.)."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the repository connection."""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: tuple = ()) -> Any:
        """Execute a query and return results."""
        pass
    
    @abstractmethod
    async def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        pass
    
    @abstractmethod
    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        pass
