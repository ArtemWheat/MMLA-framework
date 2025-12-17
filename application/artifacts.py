"""Artifact persistence helpers hooking into prediction outcomes."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from uuid import uuid4

from core.domain import PredictionOutcome, PredictionStage
from core.domain.value_objects import ArtifactRef
from core.interfaces import IArtifactStorage, IFileStorage


logger = logging.getLogger(__name__)


@dataclass
class ArtifactPolicy:
    save_depth_preview: bool = True
    save_result_json: bool = True
    target_directory: Path = Path(".")


@dataclass
class ArtifactPersistence:
    file_storage: IFileStorage
    artifact_storage: IArtifactStorage
    policy: ArtifactPolicy = field(default_factory=ArtifactPolicy)

    @staticmethod
    def _slugify_segment(segment: str) -> str:
        cleaned = segment.strip().replace("\\", "/")
        cleaned = cleaned.replace(" ", "_")
        safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in cleaned)
        return safe or "unknown"

    def _resolve_target_dir(self, outcome: PredictionOutcome, base_dir: Path) -> Path:
        if not isinstance(outcome.result, dict):
            return base_dir
        subdir = outcome.result.get("artifact_subdir")
        if not subdir:
            return base_dir
        parts = []
        for segment in str(subdir).split("/"):
            segment = segment.strip()
            if not segment or segment in (".", ".."):
                continue
            parts.append(self._slugify_segment(segment))
        if not parts:
            return base_dir
        return base_dir / Path(*parts)

    def _normalize_filename(self, filename: str, default_ext: str) -> str:
        path = Path(filename)
        name = path.name
        if not name:
            name = f"artifact{default_ext}"
        suffix = Path(name).suffix
        if suffix:
            return name
        return f"{name}{default_ext}"

    @staticmethod
    def _mime_from_extension(ext: str) -> str:
        mapping = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".bmp": "image/bmp",
            ".tif": "image/tiff",
            ".tiff": "image/tiff",
        }
        return mapping.get(ext.lower(), "application/octet-stream")

    async def handle_outcome(
        self,
        outcome: PredictionOutcome,
        *,
        case_id: Optional[str] = None,
    ) -> PredictionOutcome:
        """Augment outcome with persisted artifact references."""
        base_dir = Path(self.policy.target_directory)
        if case_id:
            base_dir = base_dir / self._slugify_segment(str(case_id))

        artifacts = list(outcome.artifacts)

        if not outcome.success:
            logger.debug(
                "Outcome stage=%s succeeded=%s; attempting to persist diagnostic artifacts.",
                outcome.stage,
                outcome.success,
            )
            source_artifact = await self._store_source_image(outcome, base_dir)
            if source_artifact:
                artifacts.append(source_artifact)
            outcome.artifacts = tuple(artifacts)  # type: ignore[attr-defined]
            return outcome

        logger.info(
            "Persisting artifacts for stage=%s prediction_id=%s",
            outcome.stage,
            outcome.prediction_id,
        )

        if self.policy.save_depth_preview:
            preview = await self._store_preview(outcome, base_dir)
            if preview:
                artifacts.append(preview)
            detection_overlay = await self._store_detection_overlay(outcome, base_dir)
            if detection_overlay:
                artifacts.append(detection_overlay)

        summary_artifact = await self._store_accuracy_summary(outcome, base_dir)
        if summary_artifact:
            artifacts.append(summary_artifact)

        if self.policy.save_result_json:
            result_artifact = await self._store_result(outcome, base_dir)
            if result_artifact:
                artifacts.append(result_artifact)

        source_artifact = await self._store_source_image(outcome, base_dir)
        if source_artifact:
            artifacts.append(source_artifact)

        outcome.artifacts = tuple(artifacts)  # type: ignore[attr-defined]
        return outcome

    async def _store_preview(self, outcome: PredictionOutcome, base_dir: Path) -> Optional[ArtifactRef]:
        if not isinstance(outcome.result, dict):
            return None
        preview_bytes = outcome.result.get("preview_bytes")
        if not preview_bytes:
            logger.debug("No preview bytes present for outcome stage=%s; skipping preview artifact.", outcome.stage)
            return None
        target_dir = self._resolve_target_dir(outcome, base_dir)
        filename_value = outcome.result.pop("preview_filename", None)
        if filename_value:
            filename = self._normalize_filename(str(filename_value), ".png")
        else:
            filename = f"preview_{outcome.stage.value}_{uuid4().hex}.png"
        mime = self._mime_from_extension(Path(filename).suffix or ".png")
        artifact = ArtifactRef(
            uri=str(target_dir / filename),
            kind=mime,
        )
        await self.artifact_storage.store(artifact=artifact, payload=preview_bytes)
        logger.info("Stored preview artifact at %s", artifact.uri)
        outcome.result.pop("preview_bytes", None)
        outcome.result["preview_uri"] = artifact.uri
        return artifact

    async def _store_detection_overlay(self, outcome: PredictionOutcome, base_dir: Path) -> Optional[ArtifactRef]:
        if not isinstance(outcome.result, dict):
            return None
        overlay_bytes = outcome.result.get("detection_overlay_bytes")
        if not overlay_bytes:
            logger.debug("No detection overlay bytes present for outcome stage=%s; skipping detection artifact.", outcome.stage)
            return None
        target_dir = self._resolve_target_dir(outcome, base_dir)
        filename_value = outcome.result.get("detection_overlay_filename")
        if filename_value:
            filename = self._normalize_filename(str(filename_value), ".png")
        else:
            filename = f"detection_overlay_{outcome.stage.value}_{uuid4().hex}.png"
        mime = self._mime_from_extension(Path(filename).suffix or ".png")
        artifact = ArtifactRef(
            uri=str(target_dir / filename),
            kind=mime,
        )
        await self.artifact_storage.store(artifact=artifact, payload=overlay_bytes)
        logger.info("Stored detection overlay artifact at %s", artifact.uri)
        outcome.result.pop("detection_overlay_bytes", None)
        outcome.result.pop("detection_overlay_filename", None)
        outcome.result["detection_overlay_uri"] = artifact.uri
        return artifact


    async def _store_source_image(self, outcome: PredictionOutcome, base_dir: Path) -> Optional[ArtifactRef]:
        if not isinstance(outcome.result, dict):
            return None

        subdir = outcome.result.get("artifact_subdir")
        if not subdir and outcome.result.get("reason"):
            subdir = f"reject/{self._slugify_segment(str(outcome.result['reason']))}"
            outcome.result["artifact_subdir"] = subdir

        if not subdir:
            return None

        segments = [segment for segment in Path(str(subdir)).parts if segment]
        if "reject" not in segments:
            return None

        source_path_value = outcome.result.get("source_path")
        if not source_path_value:
            return None

        source_path = Path(str(source_path_value))
        if not source_path.exists():
            logger.debug("Source path %s does not exist; skipping source artifact.", source_path)
            return None

        filename = self._normalize_filename(source_path.name, source_path.suffix or ".png")
        target_dir = self._resolve_target_dir(outcome, base_dir)
        mime = self._mime_from_extension(Path(filename).suffix or ".png")
        artifact = ArtifactRef(uri=str(target_dir / filename), kind=mime)

        try:
            payload = await asyncio.to_thread(source_path.read_bytes)
        except OSError:
            logger.exception("Failed to read source image %s for artifact storage.", source_path)
            return None

        await self.artifact_storage.store(artifact=artifact, payload=payload)
        logger.info("Stored source artifact at %s", artifact.uri)
        outcome.result.setdefault("source_artifact_uri", artifact.uri)
        return artifact

    async def _store_accuracy_summary(self, outcome: PredictionOutcome, base_dir: Path) -> Optional[ArtifactRef]:
        if not isinstance(outcome.result, dict):
            return None
        if not outcome.result.get("evaluation_complete"):
            return None
        summary = outcome.result.get("evaluation_summary")
        if not summary:
            return None
        try:
            payload = json.dumps(summary, ensure_ascii=False, indent=2, default=str).encode("utf-8")
        except TypeError:
            logger.warning("Evaluation summary contains non-serializable data; skipping accuracy summary artifact.")
            return None
        filename_value = outcome.result.get("accuracy_summary_filename")
        if filename_value:
            filename = Path(str(filename_value)).name
        else:
            filename = f"accuracy_summary_{uuid4().hex}.json"
        artifact = ArtifactRef(uri=str(base_dir / filename), kind="application/json")
        await self.artifact_storage.store(artifact=artifact, payload=payload)
        outcome.result["accuracy_summary_uri"] = artifact.uri
        logger.info("Stored accuracy summary artifact at %s", artifact.uri)
        return artifact

    async def _store_result(self, outcome: PredictionOutcome, base_dir: Path) -> Optional[ArtifactRef]:
        payload = self._encode_result(outcome.result)
        if payload is None:
            logger.debug("Skipping result artifact for stage=%s: result is empty.", outcome.stage)
            return None
        artifact = ArtifactRef(
            uri=str(base_dir / f"{outcome.stage.value}_result_{uuid4().hex}.json"),
            kind="application/json",
        )
        await self.artifact_storage.store(artifact=artifact, payload=payload)
        logger.info("Stored result artifact at %s", artifact.uri)
        return artifact

    @staticmethod
    def _encode_result(result: object) -> Optional[bytes]:
        if result is None:
            return None
        try:
            return json.dumps(result, ensure_ascii=False, default=str).encode("utf-8")
        except TypeError:
            logger.warning("Result contains non-serializable data; storing stringified fallback.")
            return json.dumps({"value": str(result)}, ensure_ascii=False).encode("utf-8")
