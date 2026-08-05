#!/usr/bin/env python3
"""
run_authenticity_benchmark.py
=============================
Runs the DOCUMENT_AUTHENTICITY_CHECK benchmark through the REAL validator
(via ValidatorFactory, exactly as the application dispatches it) and reports the
measured localized-ELA statistics for every image, so ELA_THRESHOLD and the
score weights can be calibrated on data instead of guesses.

Usage:
    python run_authenticity_benchmark.py
"""

from __future__ import annotations

import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.constants import ELA_THRESHOLD
from app.core.logger import get_logger
from app.factory.validator_factory import ValidatorFactory
from app.models.enums import EvidenceType, InspectionAreaType, JobType
from app.models.request import Evidence, ValidationContext, ValidationRequest

logger = get_logger("authenticity_benchmark")

BENCHMARK_DIR = Path(__file__).resolve().parent / "samples" / "images" / "authenticity_benchmark"
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


@dataclass
class Row:
    name: str
    is_tampered: bool          # ground truth
    localized: float
    contrast: float
    score: int
    detected: bool             # validator's decision at current ELA_THRESHOLD
    tamper_type: str = ""


def discover(directory: Path):
    for json_path in sorted(directory.glob("*.json")):
        image = None
        for suffix in IMAGE_SUFFIXES:
            candidate = json_path.with_suffix(suffix)
            if candidate.exists():
                image = candidate
                break
        if image is None:
            continue  # report files etc.
        label = json.loads(json_path.read_text(encoding="utf-8"))
        yield json_path.stem, image, label


def build_request(stem: str, image: Path) -> ValidationRequest:
    return ValidationRequest(
        jobId=f"authbench-{stem}",
        jobType=JobType.DOCUMENT_AUTHENTICITY_CHECK,
        evidence=Evidence(
            evidenceId=f"ev-{stem}",
            evidenceType=EvidenceType.DOCUMENT,
            fileUrl=str(image),
            mimeType="image/jpeg",
            fileSize=image.stat().st_size,
            capturedAt=datetime.now(timezone.utc),
            latitude=0.0, longitude=0.0, gpsAccuracyM=1.0,
        ),
        context=ValidationContext(
            taskId="authbench", questionId="authbench",
            inspectionAreaType=InspectionAreaType.OFFICE,
        ),
        requestJson={},
    )


def evaluate(stem: str, image: Path, label: dict) -> Row:
    validator = ValidatorFactory.get_validator(JobType.DOCUMENT_AUTHENTICITY_CHECK)
    result = validator.validate(build_request(stem, image))
    res = result.result or {}
    return Row(
        name=stem,
        is_tampered=(label.get("category") == "tampered"),
        localized=float(res.get("elaMeanScore", 0.0) or 0.0),
        contrast=float(res.get("elaMaxScore", 0.0) or 0.0),
        score=int(res.get("authenticityScore", 0) or 0),
        detected=bool(res.get("tamperingSuspected", False)),
        tamper_type=label.get("tamperType", ""),
    )


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def print_table(rows: list[Row]) -> None:
    print(f"\nELA_THRESHOLD (current) = {ELA_THRESHOLD}\n")
    print(f"| {'Image':<38} | {'Type':<9} | {'Localized':>9} | "
          f"{'Contrast':>8} | {'Score':>5} | {'Detected':>8} |")
    print(f"|{'-'*40}|{'-'*11}|{'-'*11}|{'-'*10}|{'-'*7}|{'-'*10}|")
    for r in sorted(rows, key=lambda x: (x.is_tampered, x.name)):
        typ = "TAMPERED" if r.is_tampered else "AUTHENTIC"
        print(f"| {r.name:<38} | {typ:<9} | {r.localized:>9.2f} | "
              f"{r.contrast:>8.2f} | {r.score:>5} | {str(r.detected):>8} |")


def calibration_summary(rows: list[Row]) -> dict:
    auth = [r.localized for r in rows if not r.is_tampered]
    tamp = [(r.name, r.localized) for r in rows if r.is_tampered]
    max_auth = max(auth) if auth else 0.0
    separable = [(n, v) for n, v in tamp if v > max_auth]
    # A threshold above the busiest authentic doc catches only clearly-separable tampers.
    suggested = round(max_auth + 0.5, 2) if separable else None
    return {
        "authenticLocalizedMax": round(max_auth, 2),
        "authenticLocalizedRange": [round(min(auth), 2), round(max(auth), 2)] if auth else None,
        "tamperedAboveAuthenticMax": [n for n, _ in separable],
        "tamperedBelowAuthenticMax": [n for n, v in tamp if v <= max_auth],
        "suggestedThreshold": suggested,
    }


def write_reports(rows: list[Row], summary: dict, directory: Path) -> None:
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "elaThreshold": ELA_THRESHOLD,
        "totalImages": len(rows),
        "authentic": sum(1 for r in rows if not r.is_tampered),
        "tampered": sum(1 for r in rows if r.is_tampered),
        "calibration": summary,
        "rows": [r.__dict__ for r in rows],
    }
    (directory / "authenticity_benchmark_report.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with (directory / "authenticity_benchmark_results.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["image", "type", "tamperType", "localized", "contrast", "score", "detected"])
        for r in rows:
            w.writerow([r.name, "tampered" if r.is_tampered else "authentic",
                        r.tamper_type, r.localized, r.contrast, r.score, r.detected])

    md = ["# Document Authenticity Benchmark Report", "",
          f"_ELA_THRESHOLD = {ELA_THRESHOLD}_", "",
          "| Image | Type | Localized Error | Hotspot Contrast | Score | Tampering Detected |",
          "|-------|------|----------------:|-----------------:|------:|:------------------:|"]
    for r in sorted(rows, key=lambda x: (x.is_tampered, x.name)):
        md.append(f"| {r.name} | {'TAMPERED' if r.is_tampered else 'AUTHENTIC'} | "
                  f"{r.localized:.2f} | {r.contrast:.2f} | {r.score} | {r.detected} |")
    md += ["", "## Calibration", "",
           f"- Authentic localized-error range: {summary['authenticLocalizedRange']}",
           f"- Max authentic localized error: **{summary['authenticLocalizedMax']}**",
           f"- Tampered docs above that max (ELA-separable): {summary['tamperedAboveAuthenticMax']}",
           f"- Tampered docs at/below it (NOT ELA-separable): {summary['tamperedBelowAuthenticMax']}",
           f"- Suggested ELA_THRESHOLD (catches separable tampers only): "
           f"**{summary['suggestedThreshold']}**", ""]
    (directory / "authenticity_benchmark_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    if not BENCHMARK_DIR.exists():
        print(f"Benchmark directory not found: {BENCHMARK_DIR}")
        return 1
    rows = [evaluate(stem, image, label) for stem, image, label in discover(BENCHMARK_DIR)]
    if not rows:
        print("No benchmark documents found.")
        return 1

    print_table(rows)
    summary = calibration_summary(rows)
    write_reports(rows, summary, BENCHMARK_DIR)

    print("\n--- Calibration ---")
    print(f"Authentic localized error: {summary['authenticLocalizedRange']} "
          f"(max {summary['authenticLocalizedMax']})")
    print(f"ELA-separable tampers : {summary['tamperedAboveAuthenticMax']}")
    print(f"NOT separable by ELA  : {summary['tamperedBelowAuthenticMax']}")
    print(f"Suggested threshold   : {summary['suggestedThreshold']}")
    print(f"\nReports written to {BENCHMARK_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
