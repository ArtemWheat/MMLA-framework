"""Command-line interface for managing MMLA cases."""

from __future__ import annotations

import argparse
import asyncio
import logging
import contextlib
import sys
from typing import Mapping, Sequence

from application import create_runtime
from core.domain import CaseId


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mmla", description="Manage MMLA streaming cases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available cases.")

    run_parser = subparsers.add_parser("run", help="Activate a case and keep it running until interrupted.")
    run_parser.add_argument("case_id", help="Identifier of the case to activate.")
    run_parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Optional duration in seconds to run before shutting down automatically.",
    )
    run_parser.add_argument(
        "--device-serial",
        action="append",
        default=[],
        metavar="CASE=SERIAL",
        help="Override device serial for a case (can be repeated).",
    )
    run_parser.add_argument(
        "--metadata",
        action="append",
        default=[],
        metavar="CASE:KEY=VALUE",
        help="Attach metadata key/value to case handler (can be repeated).",
    )

    subparsers.add_parser("version", help="Display CLI version information.")

    return parser


async def _list_cases() -> None:
    runtime = await create_runtime()
    try:
        cases: Sequence[CaseId] = runtime.registered_cases
        if not cases:
            print("No cases registered.")
            return
        print("Registered cases:")
        for case_id in cases:
            print(f"  - {case_id}")
    finally:
        await runtime.shutdown()


def _parse_device_serials(items: Sequence[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid device serial override '{item}'. Expected CASE=SERIAL.")
        case, serial = item.split("=", 1)
        case = case.strip()
        serial = serial.strip()
        if not case or not serial:
            raise ValueError(f"Invalid device serial override '{item}'. Expected CASE=SERIAL.")
        overrides[case] = serial
    return overrides


def _parse_metadata(items: Sequence[str]) -> dict[str, dict[str, object]]:
    overrides: dict[str, dict[str, object]] = {}
    for item in items:
        if ":" not in item or "=" not in item:
            raise ValueError(f"Invalid metadata override '{item}'. Expected CASE:KEY=VALUE.")
        case_part, rest = item.split(":", 1)
        key, value = rest.split("=", 1)
        case = case_part.strip()
        key = key.strip()
        value = value.strip()
        if not case or not key:
            raise ValueError(f"Invalid metadata override '{item}'. Expected CASE:KEY=VALUE.")
        overrides.setdefault(case, {})[key] = value
    return overrides


async def _run_case(
    case_id: str,
    duration: float | None = None,
    *,
    device_serials: Mapping[str, str] | None = None,
    metadata: Mapping[str, Mapping[str, object]] | None = None,
) -> None:
    runtime = await create_runtime(device_serials=device_serials, metadata=metadata)
    case_manager = runtime.case_manager
    case_id_obj = CaseId(case_id)
    try:
        await case_manager.activate(case_id_obj)
        print(f"Case {case_id} activated. Press Ctrl+C to stop.")
        if duration is None:
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nInterrupted, shutting down...")
        else:
            await asyncio.sleep(duration)
            print(f"\nDuration {duration}s reached, shutting down...")
    finally:
        with contextlib.suppress(Exception):
            await case_manager.deactivate_all()
        await runtime.shutdown()


def _print_version() -> None:
    from importlib.metadata import version, PackageNotFoundError

    try:
        pkg_version = version("mmla-framework")
    except PackageNotFoundError:
        pkg_version = "0.0.0-dev"
    print(f"MMLA CLI version {pkg_version}")


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        force=True,
    )
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        asyncio.run(_list_cases())
        return 0

    if args.command == "run":
        try:
            device_serials = _parse_device_serials(args.device_serial)
            metadata = _parse_metadata(args.metadata)
        except ValueError as exc:
            parser.error(str(exc))
        asyncio.run(
            _run_case(
                args.case_id,
                duration=args.duration,
                device_serials=device_serials or None,
                metadata=metadata or None,
            )
        )
        return 0

    if args.command == "version":
        _print_version()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
