"""Hash-verified Grafana CSV normalization and descriptive coverage audit.

No interpolation, outage inference, or source-of-power inference.
Python 3.12; standard library only. Registry and input manifests are controlled.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HEADER = re.compile(r"^(Voltage|Frequency) ([0-9A-Fa-f]{8}) \((.+)\)$")
FIELDS = ["source_export_id", "source_row_number", "time_source", "time_utc",
          "site_id", "sensor_id", "circuit_id", "mapping_status", "metric",
          "unit", "raw_value", "value", "observation_status", "qa_flags"]
COVERAGE_FIELDS = ["source_export_id", "site_id", "sensor_id", "metric", "expected_slots",
                   "unambiguous_numeric_slots", "missing_measurement_slots", "conflicting_slots",
                   "qa_flagged_slots", "duplicate_extra_records", "numeric_coverage_percent",
                   "longest_missing_slot_run_seconds"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_value(raw: str) -> tuple[float | None, str]:
    if raw.strip().casefold() in {"", "null", "none", "nan", "n/a", "na"}:
        return None, "missing_measurement"
    try:
        value = float(raw)
    except ValueError:
        return None, "invalid_value"
    if not math.isfinite(value):
        return None, "invalid_value"
    return value, "numeric_observation"


def parse_time(raw: str, timezone_name: str, time_format: str) -> datetime:
    if time_format == "unix_ms":
        return datetime.fromtimestamp(float(raw) / 1000, timezone.utc)
    if time_format != "local_string":
        raise ValueError(f"Unsupported explicit timestamp format: {time_format}")
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
    return parsed.astimezone(timezone.utc)


def observation_flags(metric: str, value: float | None,
                      paired_voltage: float | None, screen: dict) -> list[str]:
    if value is None:
        return []
    flags = []
    low = screen["low_voltage_candidate_below_V"]
    if metric == "voltage":
        if value < 0:
            flags.append("negative_voltage_review")
        if value < low:
            flags.append("low_voltage_candidate_not_verified_outage")
    else:
        if paired_voltage is not None and paired_voltage < low:
            flags.append("frequency_with_low_voltage_not_interpretable")
        if (value < screen["frequency_review_below_Hz"] or
                value > screen["frequency_review_above_Hz"]):
            flags.append("frequency_outside_screen_review")
    return flags


def longest_missing_run(slots: list[datetime], observed: set[datetime]) -> int:
    longest = current = 0
    for slot in slots:
        current = 0 if slot in observed else current + 1
        longest = max(longest, current)
    return longest


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build(manifest_path: Path, registry_path: Path, out: Path) -> dict:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "config/powerwatch_event.json"
    config = json.loads(config_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    registry = json.loads(registry_path.read_text())
    zone = config["source_timezone"]
    interval = config["expected_interval_seconds"]
    mapping = {}
    for item in registry["sensors"]:
        for label in item["dashboard_aliases"]:
            key = (label.casefold(), item["source_sensor_serial"].upper())
            if key in mapping:
                raise ValueError("Ambiguous registry mapping; reconcile deployments first")
            mapping[key] = item
    records, exports, coverage, site_returns = [], [], [], []
    seen_export_ids = set()
    for source in manifest["exports"]:
        if not source["active_for_pipeline"]:
            continue
        if source["export_id"] in seen_export_ids:
            raise ValueError("Duplicate export ID in manifest")
        seen_export_ids.add(source["export_id"])
        path = root / source["relative_path"]
        digest = sha256(path)
        if digest != source["sha256"]:
            raise ValueError(f"Source hash mismatch: {source['export_id']}")
        start = parse_time(source["query_start_local"], zone, "local_string")
        end = parse_time(source["query_end_exclusive_local"], zone, "local_string")
        if end <= start or end - start > timedelta(days=config["export_window_max_days"]):
            raise ValueError("Export window must be positive and at most seven days")
        first_epoch = math.ceil(start.timestamp() / interval) * interval
        slots = []
        slot = datetime.fromtimestamp(first_epoch, timezone.utc)
        while slot < end:
            slots.append(slot)
            slot += timedelta(seconds=interval)
        if not slots:
            raise ValueError("Export query contains no expected sampling slots")
        expected = set(slots)
        groups = defaultdict(list)
        returned_sites = set()
        time_issues = []
        source_flags = Counter()
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or reader.fieldnames[0] != "Time":
                raise ValueError("Expected explicit Time column in Grafana CSV")
            columns = []
            for column in reader.fieldnames[1:]:
                match = HEADER.fullmatch(column)
                if not match:
                    raise ValueError(f"Unrecognized measurement column: {column}")
                metric, serial, label = match.groups()
                key = (label.casefold(), serial.upper())
                if key not in mapping:
                    raise ValueError(f"Unmapped sensor column: {column}")
                item = mapping[key]
                columns.append((column, metric.lower(), serial.upper(), item))
                returned_sites.add(item["site_id"])
            input_row_count = 0
            for row_number, row in enumerate(reader, 2):
                input_row_count += 1
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f"Malformed CSV row at source line {row_number}")
                raw_time = row["Time"]
                try:
                    timestamp = parse_time(raw_time, zone, source["timestamp_format"])
                except (ValueError, OverflowError) as exc:
                    time_issues.append({"source_export_id": source["export_id"],
                                        "source_row_number": row_number,
                                        "time_source": raw_time, "issue": str(exc)})
                    continue
                voltages = {serial: parse_value(row[column])[0]
                            for column, metric, serial, _ in columns if metric == "voltage"}
                for column, metric, serial, item in columns:
                    value, status = parse_value(row[column])
                    flags = observation_flags(metric, value, voltages.get(serial), config["qa_screen"])
                    if timestamp not in expected:
                        flags.append("timestamp_outside_expected_grid")
                    source_flags.update(flags)
                    record = dict(zip(FIELDS, [source["export_id"], row_number, raw_time,
                        timestamp.isoformat().replace("+00:00", "Z"), item["site_id"],
                        item["sensor_id"], item["circuit_id"], item["mapping_status"],
                        metric, "V" if metric == "voltage" else "Hz", row[column],
                        value, status, ";".join(flags)]))
                    records.append(record)
                    groups[(item["site_id"], item["sensor_id"], metric, timestamp)].append(record)
        series_keys = sorted({key[:3] for key in groups})
        duplicate_rows = conflicts = 0
        for site, sensor, metric in series_keys:
            numeric_slots, nonmissing_slots, conflict_slots, flagged_slots = set(), set(), set(), set()
            duplicate_count = 0
            for (gsite, gsensor, gmetric, timestamp), group in groups.items():
                if (gsite, gsensor, gmetric) != (site, sensor, metric):
                    continue
                duplicate_count += max(0, len(group) - 1)
                values = {record["value"] for record in group if record["value"] is not None}
                if len(values) > 1:
                    conflict_slots.add(timestamp)
                    for record in group:
                        record["qa_flags"] = ";".join(filter(None, [record["qa_flags"], "conflicting_duplicate"]))
                elif values:
                    numeric_slots.add(timestamp)
                if any(record["observation_status"] != "missing_measurement" for record in group):
                    nonmissing_slots.add(timestamp)
                if any(record["qa_flags"] for record in group):
                    flagged_slots.add(timestamp)
            numeric_slots &= expected
            nonmissing_slots &= expected
            conflict_slots &= expected
            denominator = len(slots)
            coverage.append({"source_export_id": source["export_id"], "site_id": site,
                "sensor_id": sensor, "metric": metric, "expected_slots": denominator,
                "unambiguous_numeric_slots": len(numeric_slots),
                "missing_measurement_slots": len(expected - nonmissing_slots),
                "conflicting_slots": len(conflict_slots), "qa_flagged_slots": len(flagged_slots & expected),
                "duplicate_extra_records": duplicate_count,
                "numeric_coverage_percent": round(100 * len(numeric_slots) / denominator, 4),
                "longest_missing_slot_run_seconds": interval * longest_missing_run(slots, nonmissing_slots)})
            duplicate_rows += duplicate_count
            conflicts += len(conflict_slots)
        for site in source["selected_site_ids"]:
            site_returns.append({"source_export_id": source["export_id"], "site_id": site,
                "returned_series": site in returned_sites,
                "interpretation": "series_returned" if site in returned_sites else "no_series_returned_not_outage_evidence"})
        exports.append({"source_export_id": source["export_id"], "sha256": digest,
                        "input_rows": input_row_count, "measurement_columns": len(columns),
                        "returned_site_count": len(returned_sites), "time_issues": time_issues,
                        "duplicate_extra_records": duplicate_rows, "conflicting_slots": conflicts,
                        "qa_flag_observations": dict(source_flags),
                        "formatted_export": source["formatted_data"],
                        "measurement_scope": "dashboard_export_not_database_dump"})
    if not exports:
        raise ValueError("No active exports")
    # Retain both original records when overlapping exports disagree.
    global_groups = defaultdict(list)
    for record in records:
        key = tuple(record[field] for field in ["site_id", "sensor_id", "metric", "time_utc"])
        global_groups[key].append(record)
    cross_export_conflicts = 0
    for group in global_groups.values():
        if len({r["source_export_id"] for r in group}) > 1 and len({r["value"] for r in group if r["value"] is not None}) > 1:
            cross_export_conflicts += 1
            for record in group:
                record["qa_flags"] = ";".join(filter(None, [record["qa_flags"], "conflicting_export_overlap"]))
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "readings.csv", FIELDS, records)
    write_csv(out / "coverage.csv", COVERAGE_FIELDS, coverage)
    write_csv(out / "selected_site_returns.csv", list(site_returns[0]), site_returns)
    report = {"package_version": config["package_version"], "python_requirement": "3.12",
        "python_version_used": platform.python_version(),
        "release_status": "pseudonymous_derivative_raw_identity_files_controlled", "source_timezone": zone,
        "record_count": len(records), "cross_export_conflicting_slots": cross_export_conflicts,
        "source_manifest_sha256": sha256(manifest_path), "registry_sha256": sha256(registry_path),
        "configuration_sha256": sha256(config_path), "pipeline_sha256": sha256(Path(__file__)),
        "exports": exports, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_sha256": {p.name: sha256(p) for p in sorted(out.glob("*.csv"))},
        "interpretation": "Coverage describes returned observations, not verified electrical availability or oxygen delivery"}
    (out / "run_provenance.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.manifest.resolve(), args.registry.resolve(), args.out.resolve())
    print(json.dumps({"record_count": report["record_count"], "exports": len(report["exports"]),
                      "cross_export_conflicting_slots": report["cross_export_conflicting_slots"],
                      "release_status": report["release_status"]}, indent=2))
