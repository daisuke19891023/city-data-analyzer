"""Compile InteractiveAnalysisProgram with DSPy Optimizer style pipeline."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import structlog

from city_data_backend.services.optimization import OptimizationService

logger = structlog.get_logger()


def compile_program(trainset_path: Path, output_path: Path, version: str) -> None:
    """Compile interactive pipeline and persist artifact."""
    logger.info(
        "Starting interactive compilation",
        trainset=str(trainset_path),
        output=str(output_path),
        version=version,
    )
    service = OptimizationService()
    service.compile_interactive(
        trainset_path,
        version=version,
        output_path=output_path,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trainset",
        type=Path,
        default=Path("apps/python-backend/dspy/interactive/trainset_samples.json"),
        help="Path to curated trainset JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("apps/python-backend/dspy/interactive/compiled_program.json"),
        help="Where to write compiled artifact",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=f"interactive-compiled-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
    )
    args = parser.parse_args()
    compile_program(args.trainset, args.output, args.version)
