"""Explicit adapters for perturbation scoring reports, never arbitrary JSON."""
from __future__ import annotations

from copy import deepcopy

SCHEMA_VERSION = "perturbation-scoring-v2"
PROXY_EVIDENCE = "Fixed factor inventory and intended damage in target_factor_groups/operations; not text inference."


def normalize_metrics(metrics: dict) -> dict:
    result = dict(metrics)
    if "lemon_full" in result:
        old = result.pop("lemon_full")
        if "factor_damage_proxy" in result and result["factor_damage_proxy"] != old:
            raise ValueError("Conflicting lemon_full and factor_damage_proxy values")
        result["factor_damage_proxy"] = old
    return result


def normalize_scoring_report(report: dict) -> dict:
    """Read a v2 report or a structurally identified legacy scoring report."""
    schema = report.get("schema_version")
    if schema not in (None, SCHEMA_VERSION):
        raise ValueError(f"Unsupported perturbation report schema: {schema}")
    if not all(key in report for key in ("input", "inventory", "rows", "summary", "metrics")):
        raise ValueError("Expected a perturbation scoring report with input, inventory, rows, summary and metrics")
    result = deepcopy(report)
    for row in result["rows"]:
        row["scores"] = normalize_metrics(row["scores"])
    for row in result["summary"]:
        row["metrics"] = normalize_metrics(row["metrics"])
    result["metrics"] = list(dict.fromkeys(
        "factor_damage_proxy" if name == "lemon_full" else name for name in result["metrics"]
    ))
    result["schema_version"] = SCHEMA_VERSION
    result["proxy_evidence"] = PROXY_EVIDENCE
    return result


def normalize_sensitivity_report(report: dict) -> dict:
    """Adapter for the specific compact sensitivity format."""
    schema = report.get("schema_version")
    if schema not in (None, "perturbation-sensitivity-v2"):
        raise ValueError(f"Unsupported sensitivity schema: {schema}")
    if not all(key in report for key in ("metrics", "by_variant", "by_dataset", "by_dataset_variant")):
        raise ValueError("Expected compact perturbation sensitivity report")
    result = deepcopy(report)
    for key in ("by_variant", "by_dataset", "by_dataset_variant"):
        result[key] = [normalize_metrics(row) for row in result[key]]
    result["metrics"] = list(dict.fromkeys(
        "factor_damage_proxy" if name == "lemon_full" else name for name in result["metrics"]
    ))
    result["schema_version"] = "perturbation-sensitivity-v2"
    result["proxy_evidence"] = PROXY_EVIDENCE
    return result
