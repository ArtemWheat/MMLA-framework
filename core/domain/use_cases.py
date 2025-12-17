"""Use-case abstractions for orchestrating pipeline actions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class UseCase(ABC, Generic[TRequest, TResponse]):
    """Generic synchronous use-case contract."""

    @abstractmethod
    def execute(self, request: TRequest) -> TResponse:
        """Execute the use-case."""


class AsyncUseCase(ABC, Generic[TRequest, TResponse]):
    """Generic async use-case contract."""

    @abstractmethod
    async def execute(self, request: TRequest) -> TResponse:
        """Execute the use-case asynchronously."""
