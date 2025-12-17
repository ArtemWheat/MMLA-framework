"""Interface definitions for the framework."""

from core.interfaces.events import IEventBus
from core.interfaces.predictors import BaseAnalyticsPredictor, BasePredictor, BaseValidationPredictor
from core.interfaces.repositories import IArtifactStorage, IFileStorage, IRepositoryDB, IUnitOfWork
from core.interfaces.streams import (
    BaseStreamHandler,
    ChannelSpec,
    IDeviceProbe,
    IFrameMuxer,
    IMultiChannelFrame,
    IStreamHandler,
    StreamDescriptor,
)

__all__ = [
    "BaseStreamHandler",
    "ChannelSpec",
    "IStreamHandler",
    "IFrameMuxer",
    "IMultiChannelFrame",
    "IDeviceProbe",
    "StreamDescriptor",
    "BasePredictor",
    "BaseValidationPredictor",
    "BaseAnalyticsPredictor",
    "IRepositoryDB",
    "IUnitOfWork",
    "IFileStorage",
    "IArtifactStorage",
    "IEventBus",
]
