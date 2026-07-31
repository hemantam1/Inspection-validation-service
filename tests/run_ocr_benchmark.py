#!/usr/bin/env python3
"""
run_ocr_benchmark.py
====================
Official regression benchmark for the OCR validator.

It drives the EXISTING OCR validator exactly as the application does — via
`ValidatorFactory.get_validator(JobType.OCR_CHECK).validate(request)` — so no
OCR logic is duplicated here. It discovers every labelled sample under
samples/images/ocr_benchmark/, runs the validator, compares the validator's
decision against the expected label, writes JSON / Markdown / CSV reports,
prints a colored terminal summary, and exits non-zero if any sample fails
(so it can gate CI / GitHub Actions).

Usage:
    python run_ocr_benchmark.py

Exit codes:
    0 - every sample passed
    1 - one or more samples failed (or no samples found)
"""

from __future__ import annotations

import csv
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# --- application imports (the validator is used, never re-implemented) -------
from app.core.logger import get_logger
from app.factory.validator_factory import ValidatorFactory
from app.models.enums import EvidenceType, InspectionAreaType, JobType
from app.models.request import Evidence, ValidationContext, ValidationRequest

logger = get_logger("ocr_benchmark")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BENCHMARK_DIR = PROJECT_ROOT / "samples" / "images" / "ocr_benchmark"
REPORTS_DIR = BENCHMARK_DIR
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")


# --------------------------------------------------------------------------- #
# Terminal colors (no external dependency; respects NO_COLOR / non-tty)
# --------------------------------------------------------------------------- #
class C:
    enabled = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
    if os.name == "nt":
        os.system("")  # enable ANSI escape processing on Windows 10+

    @classmethod
    def _w(cls, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if cls.enabled else text

    @classmethod
    def green(cls, t): return cls._w("32", t)
    @classmethod
    def red(cls, t): return cls._w("31", t)
    @classmethod
    def yellow(cls, t): return cls._w("33", t)
    @classmethod
    def cyan(cls, t): return cls._w("36", t)
    @classmethod
    def bold(cls, t): return cls._w("1", t)


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class SampleResult:
    name: str
    category: str
    difficulty: str
    expected_matched: bool
    actual_matched: bool
    expected_score: Optional[float]
    actual_score: float
    ocr_confidence: float
    validator_error: Optional[str] = None
    status: str = ""       # TP | TN | FP | FN
    passed: bool = False
    deviation: float = 0.0

    def classify(self) -> None:
        e, a = self.expected_matched, self.actual_matched
        self.status = {
            (True, True): "TP",
            (False, False): "TN",
            (False, True): "FP",
            (True, False): "FN",
        }[(e, a)]
        self.passed = e == a
        if self.expected_score is not None:
            self.deviation = round(abs(self.actual_score - self.expected_score), 2)


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #
def find_image_for(json_path: Path) -> Optional[Path]:
    for suffix in IMAGE_SUFFIXES:
        candidate = json_path.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return None


def discover_samples(directory: Path):
    """Every *.json that has a sibling image. Report files are skipped naturally
    because they have no matching image."""
    samples = []
    for json_path in sorted(directory.glob("*.json")):
        image_path = find_image_for(json_path)
        if image_path is None:
            continue
        try:
            label = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Skipping unreadable JSON: %s", json_path.name)
            continue
        if "expectedText" not in label:
            continue
        samples.append((json_path.stem, image_path, label))
    return samples


# --------------------------------------------------------------------------- #
# Validator invocation (exactly as the application dispatches it)
# --------------------------------------------------------------------------- #
def build_request(stem: str, image_path: Path, expected_text: str) -> ValidationRequest:
    """OCR-relevant fields are real; the rest are valid placeholders the OCR
    validator ignores."""
    return ValidationRequest(
        jobId=f"benchmark-{stem}",
        jobType=JobType.OCR_CHECK,
        evidence=Evidence(
            evidenceId=stem,
            evidenceType=EvidenceType.DOCUMENT,
            fileUrl=str(image_path),
            mimeType="image/png",
            fileSize=image_path.stat().st_size,
            capturedAt=datetime.now(timezone.utc),
            latitude=0.0,
            longitude=0.0,
            gpsAccuracyM=1.0,
        ),
        context=ValidationContext(
            taskId="benchmark",
            questionId="benchmark",
            expectedText=expected_text,
            inspectionAreaType=InspectionAreaType.OFFICE,
        ),
        requestJson={},
    )


def evaluate_sample(stem: str, image_path: Path, label: dict) -> SampleResult:
    request = build_request(stem, image_path, label["expectedText"])
    validator = ValidatorFactory.get_validator(JobType.OCR_CHECK)  # app dispatch
    result = validator.validate(request)

    res = result.result or {}
    sample = SampleResult(
        name=stem,
        category=label.get("category", "uncategorized"),
        difficulty=label.get("difficulty", "unknown"),
        expected_matched=bool(label.get("expectedTextMatched", False)),
        actual_matched=bool(res.get("textMatched", False)),
        expected_score=label.get("expectedMatchScore"),
        actual_score=float(res.get("matchScore", 0.0) or 0.0),
        ocr_confidence=float(res.get("ocrConfidence", 0.0) or 0.0),
        validator_error=(result.error.code if result.error else None),
    )
    sample.classify()
    return sample


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def _group_accuracy(results, key):
    groups: dict[str, list[SampleResult]] = {}
    for r in results:
        groups.setdefault(getattr(r, key), []).append(r)
    out = {}
    for name, items in sorted(groups.items()):
        passed = sum(1 for r in items if r.passed)
        out[name] = {
            "total": len(items),
            "passed": passed,
            "failed": len(items) - passed,
            "accuracy": round(100.0 * passed / len(items), 1),
        }
    return out


def aggregate(results: list[SampleResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    avg_conf = round(sum(r.ocr_confidence for r in results) / total, 2) if total else 0.0
    avg_score = round(sum(r.actual_score for r in results) / total, 2) if total else 0.0

    worst = sorted(results, key=lambda r: (r.passed, -r.deviation))[:5]
    best = sorted(results, key=lambda r: (not r.passed, r.deviation))[:5]

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalSamples": total,
        "passed": passed,
        "failed": failed,
        "accuracy": round(100.0 * passed / total, 1) if total else 0.0,
        "averageOcrConfidence": avg_conf,
        "averageMatchScore": avg_score,
        "falsePositives": [r.name for r in results if r.status == "FP"],
        "falseNegatives": [r.name for r in results if r.status == "FN"],
        "categoryAccuracy": _group_accuracy(results, "category"),
        "difficultyAccuracy": _group_accuracy(results, "difficulty"),
        "worst5": [_sample_brief(r) for r in worst],
        "best5": [_sample_brief(r) for r in best],
    }


def _sample_brief(r: SampleResult) -> dict:
    return {
        "name": r.name,
        "status": r.status,
        "passed": r.passed,
        "expectedScore": r.expected_score,
        "actualScore": r.actual_score,
        "deviation": r.deviation,
    }


# --------------------------------------------------------------------------- #
# Report writers
# --------------------------------------------------------------------------- #
def write_json_report(summary: dict, results: list[SampleResult], path: Path) -> None:
    payload = dict(summary)
    payload["samples"] = [
        {
            "name": r.name, "category": r.category, "difficulty": r.difficulty,
            "expectedMatched": r.expected_matched, "actualMatched": r.actual_matched,
            "expectedScore": r.expected_score, "actualScore": r.actual_score,
            "ocrConfidence": r.ocr_confidence, "status": r.status,
            "passed": r.passed, "validatorError": r.validator_error,
        }
        for r in results
    ]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv_report(results: list[SampleResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "name", "category", "difficulty", "expectedMatched", "actualMatched",
            "expectedScore", "actualScore", "ocrConfidence", "status", "passed",
            "validatorError",
        ])
        for r in results:
            writer.writerow([
                r.name, r.category, r.difficulty, r.expected_matched, r.actual_matched,
                r.expected_score, r.actual_score, r.ocr_confidence, r.status, r.passed,
                r.validator_error or "",
            ])


def _md_group_table(title: str, group: dict) -> str:
    lines = [f"### {title}", "", "| Group | Passed | Total | Accuracy |",
             "|-------|:------:|:-----:|:--------:|"]
    for name, s in group.items():
        lines.append(f"| {name} | {s['passed']} | {s['total']} | {s['accuracy']}% |")
    return "\n".join(lines) + "\n"


def write_md_report(summary: dict, results: list[SampleResult], path: Path) -> None:
    s = summary
    status = "✅ PASS" if s["failed"] == 0 else "❌ FAIL"
    md = [
        "# OCR Validator Benchmark Report", "",
        f"_Generated: {s['generatedAt']}_", "",
        f"**Result: {status}**", "",
        "## Summary", "",
        "| Metric | Value |", "|--------|------:|",
        f"| Total Samples | {s['totalSamples']} |",
        f"| Passed | {s['passed']} |",
        f"| Failed | {s['failed']} |",
        f"| Accuracy | {s['accuracy']}% |",
        f"| Average OCR Confidence | {s['averageOcrConfidence']} |",
        f"| Average Match Score | {s['averageMatchScore']} |",
        f"| False Positives | {len(s['falsePositives'])} |",
        f"| False Negatives | {len(s['falseNegatives'])} |",
        "",
        _md_group_table("Category-wise accuracy", s["categoryAccuracy"]),
        _md_group_table("Difficulty-wise accuracy", s["difficultyAccuracy"]),
    ]
    if s["falsePositives"]:
        md += ["### False Positives (expected NO match, validator matched)", "",
               "".join(f"- `{n}`\n" for n in s["falsePositives"]), ""]
    if s["falseNegatives"]:
        md += ["### False Negatives (expected match, validator did not)", "",
               "".join(f"- `{n}`\n" for n in s["falseNegatives"]), ""]

    def brief_table(title, rows):
        out = [f"### {title}", "",
               "| Sample | Status | Expected | Actual | Δ |",
               "|--------|:------:|:--------:|:------:|:--:|"]
        for r in rows:
            out.append(f"| {r['name']} | {r['status']} | {r['expectedScore']} | "
                       f"{r['actualScore']} | {r['deviation']} |")
        return "\n".join(out) + "\n"

    md += [brief_table("Worst 5 samples", s["worst5"]),
           brief_table("Best 5 samples", s["best5"])]

    md += ["## All samples", "",
           "| Sample | Category | Diff | Status | Exp | Act | Score | Conf |",
           "|--------|----------|------|:------:|:---:|:---:|------:|-----:|"]
    for r in results:
        md.append(f"| {r.name} | {r.category} | {r.difficulty} | {r.status} | "
                  f"{r.expected_matched} | {r.actual_matched} | {r.actual_score} | "
                  f"{r.ocr_confidence} |")
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Terminal summary
# --------------------------------------------------------------------------- #
def print_summary(summary: dict, results: list[SampleResult]) -> None:
    s = summary
    print(C.bold("\n" + "=" * 62))
    print(C.bold("  OCR VALIDATOR BENCHMARK"))
    print(C.bold("=" * 62))

    for r in results:
        mark = C.green("PASS") if r.passed else C.red("FAIL")
        tag = {"TP": C.green, "TN": C.green, "FP": C.red, "FN": C.yellow}[r.status](r.status)
        print(f"  [{mark}] {r.name:<32} {tag}  "
              f"score={r.actual_score:>5}  conf={r.ocr_confidence:>5}")

    acc = s["accuracy"]
    acc_c = C.green if s["failed"] == 0 else (C.yellow if acc >= 80 else C.red)
    print(C.bold("-" * 62))
    print(f"  Samples : {s['totalSamples']}   "
          f"{C.green('Passed ' + str(s['passed']))}   "
          f"{C.red('Failed ' + str(s['failed']))}")
    print(f"  Accuracy: {acc_c(str(acc) + '%')}   "
          f"AvgConf: {C.cyan(str(s['averageOcrConfidence']))}   "
          f"AvgScore: {C.cyan(str(s['averageMatchScore']))}")
    print(f"  False Positives: {C.red(str(len(s['falsePositives'])))}   "
          f"False Negatives: {C.yellow(str(len(s['falseNegatives'])))}")
    if s["falsePositives"]:
        print("  " + C.red("FP: " + ", ".join(s["falsePositives"])))
    if s["falseNegatives"]:
        print("  " + C.yellow("FN: " + ", ".join(s["falseNegatives"])))
    print(C.bold("=" * 62))
    verdict = C.green("BENCHMARK PASSED") if s["failed"] == 0 else C.red("BENCHMARK FAILED")
    print("  " + C.bold(verdict))
    print(C.bold("=" * 62) + "\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    logger.info("Discovering OCR benchmark samples in %s", BENCHMARK_DIR)
    if not BENCHMARK_DIR.exists():
        print(C.red(f"Benchmark directory not found: {BENCHMARK_DIR}"))
        return 1

    samples = discover_samples(BENCHMARK_DIR)
    if not samples:
        print(C.red("No benchmark samples found (need <name>.png + <name>.json)."))
        return 1

    results: list[SampleResult] = []
    for stem, image_path, label in samples:
        try:
            results.append(evaluate_sample(stem, image_path, label))
        except Exception as exc:  # a crash on one sample must not sink the run
            logger.exception("Sample failed to evaluate: %s", stem)
            results.append(SampleResult(
                name=stem, category=label.get("category", "uncategorized"),
                difficulty=label.get("difficulty", "unknown"),
                expected_matched=bool(label.get("expectedTextMatched", False)),
                actual_matched=False, expected_score=label.get("expectedMatchScore"),
                actual_score=0.0, ocr_confidence=0.0,
                validator_error=f"RUNNER_ERROR: {type(exc).__name__}",
            ))
            results[-1].classify()

    summary = aggregate(results)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_json_report(summary, results, REPORTS_DIR / "benchmark_report.json")
    write_csv_report(results, REPORTS_DIR / "benchmark_results.csv")
    write_md_report(summary, results, REPORTS_DIR / "benchmark_report.md")
    print_summary(summary, results)
    logger.info("Reports written to %s", REPORTS_DIR)

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
