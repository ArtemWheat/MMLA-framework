"""Local filesystem storage implementations."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Optional

from core.domain import ArtifactRef
from core.interfaces import IArtifactStorage, IFileStorage


class LocalFileStorage(IFileStorage):
    """Stores raw session data on the local filesystem."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_bytes(self, *, path: str, data: bytes, overwrite: bool = False) -> ArtifactRef:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)

        def _write() -> None:
            if target.exists() and not overwrite:
                raise FileExistsError(f"File {target} already exists.")
            target.write_bytes(data)

        await asyncio.to_thread(_write)
        return ArtifactRef(uri=str(target.resolve()), kind="file")

    async def copy_tree(self, source: str, destination: str) -> None:
        src = self.root / source
        dst = self.root / destination

        def _copy() -> None:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

        await asyncio.to_thread(_copy)

    async def remove_tree(self, path: str) -> None:
        target = self.root / path

        def _remove() -> None:
            if target.exists():
                shutil.rmtree(target)

        await asyncio.to_thread(_remove)


class LocalArtifactStorage(IArtifactStorage):
    """Stores processed artifacts (images, JSON, etc.) on the local filesystem."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, artifact: ArtifactRef) -> Path:
        if artifact.uri.startswith("file://"):
            rel_path = artifact.uri[len("file://") :]
        else:
            rel_path = artifact.uri
        return (self.root / rel_path).resolve()

    async def store(self, *, artifact: ArtifactRef, payload: bytes) -> None:

        target = self._resolve(artifact)
        target.parent.mkdir(parents=True, exist_ok=True)

        await asyncio.to_thread(target.write_bytes, payload)

    async def fetch(self, artifact: ArtifactRef) -> bytes:
        target = self._resolve(artifact)
        return await asyncio.to_thread(target.read_bytes)

    async def delete(self, artifact: ArtifactRef) -> None:
        target = self._resolve(artifact)

        def _remove() -> None:
            if target.exists():
                target.unlink()

        await asyncio.to_thread(_remove)
