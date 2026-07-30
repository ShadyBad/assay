"""Validate the /assay run recorder and stats reader.

These two scripts are the only executable code Assay ships, and they exist to
make claims about whether the pipeline works. A silent bug here produces
confident numbers from corrupt data — worse than no instrumentation. So the
tests concentrate on the validation boundary (what the recorder refuses) and
on the small-sample guard (what the stats reader declines to assert).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from conftest import ROOT

SCRIPTS = ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader, f"cannot load scripts/{name}.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


record_mod = _load("assay_record")
stats_mod = _load("assay_stats")


def minimal(**overrides) -> dict:
    base = {"project": "personal", "risk_tier": "MEDIUM", "outcome": "committed"}
    base.update(overrides)
    return base


# --- recorder: required fields ------------------------------------------------


@pytest.mark.parametrize("missing", ["project", "risk_tier", "outcome"])
def test_missing_required_field_rejected(missing):
    rec = minimal()
    del rec[missing]
    with pytest.raises(record_mod.ValidationError, match=missing):
        record_mod.validate(rec)


def test_non_object_rejected():
    with pytest.raises(record_mod.ValidationError):
        record_mod.validate(["not", "an", "object"])


# --- recorder: normalization --------------------------------------------------


def test_tier_and_outcome_normalized_to_canonical_case():
    rec = record_mod.validate(minimal(risk_tier="high", outcome="COMMITTED"))
    assert rec["risk_tier"] == "HIGH"
    assert rec["outcome"] == "committed"


def test_defaults_filled_for_ts_run_id_and_verdict():
    rec = record_mod.validate(minimal())
    assert rec["run_id"]
    assert rec["ts"].endswith("Z")
    assert rec["brandon_verdict"] == "unknown"


def test_supplied_run_id_preserved():
    rec = record_mod.validate(minimal(run_id="fixed-id"))
    assert rec["run_id"] == "fixed-id"


@pytest.mark.parametrize("tier", ["EPIC", "", "high-ish"])
def test_unknown_tier_rejected(tier):
    with pytest.raises(record_mod.ValidationError, match="risk_tier"):
        record_mod.validate(minimal(risk_tier=tier))


def test_unknown_outcome_rejected():
    with pytest.raises(record_mod.ValidationError, match="outcome"):
        record_mod.validate(minimal(outcome="shipped-probably"))


def test_unknown_verdict_rejected():
    with pytest.raises(record_mod.ValidationError, match="brandon_verdict"):
        record_mod.validate(minimal(brandon_verdict="loved it"))


# --- recorder: the invariants that keep metrics honest ------------------------


def test_accepted_exceeding_concerns_rejected():
    """The whole acceptance metric collapses if a judge can accept what it never raised."""
    rec = minimal(judges=[{"judge": "security", "concerns": 1, "accepted": 2}])
    with pytest.raises(record_mod.ValidationError, match="exceeds"):
        record_mod.validate(rec)


def test_fired_stage_not_marked_eligible_rejected():
    """Fire rate above 100% means the bookkeeping is wrong, not that the stage overperformed."""
    rec = minimal(stages_fired=["judge-panel"], stages_eligible=["plan"])
    with pytest.raises(record_mod.ValidationError, match="not marked eligible"):
        record_mod.validate(rec)


def test_unknown_stage_name_rejected():
    with pytest.raises(record_mod.ValidationError, match="unknown stage"):
        record_mod.validate(minimal(stages_fired=["vibes"], stages_eligible=["vibes"]))


def test_eligible_defaults_to_fired_when_omitted():
    rec = record_mod.validate(minimal(stages_fired=["plan", "done-gate"]))
    assert rec["stages_eligible"] == ["plan", "done-gate"]


def test_judge_without_name_rejected():
    with pytest.raises(record_mod.ValidationError, match="judge"):
        record_mod.validate(minimal(judges=[{"concerns": 1}]))


@pytest.mark.parametrize("bad", [-1, "3", True, 1.5])
def test_negative_or_nonint_counts_rejected(bad):
    with pytest.raises(record_mod.ValidationError):
        record_mod.validate(minimal(judges=[{"judge": "naming", "concerns": bad}]))


def test_incomplete_diff_stat_rejected():
    with pytest.raises(record_mod.ValidationError, match="deleted"):
        record_mod.validate(minimal(diff_before_review={"files": 1, "added": 2}))


@pytest.mark.parametrize("field", ["rework_turns", "tokens_total"])
def test_negative_scalar_metrics_rejected(field):
    with pytest.raises(record_mod.ValidationError, match=field):
        record_mod.validate(minimal(**{field: -1}))


# --- recorder: writing --------------------------------------------------------


def test_append_creates_parents_and_round_trips(tmp_path):
    log = tmp_path / "nested" / "assay-runs.jsonl"
    rec = record_mod.validate(minimal(run_id="r1"))
    record_mod.append(rec, log)

    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["run_id"] == "r1"


def test_append_is_additive_not_rewriting(tmp_path):
    log = tmp_path / "assay-runs.jsonl"
    for run_id in ("r1", "r2", "r3"):
        record_mod.append(record_mod.validate(minimal(run_id=run_id)), log)
    assert len(log.read_text().strip().splitlines()) == 3


def test_main_rejects_bad_json_without_writing(tmp_path, capsys):
    log = tmp_path / "assay-runs.jsonl"
    src = tmp_path / "rec.json"
    src.write_text("{not json")

    assert record_mod.main(["--file", str(src), "--log", str(log)]) == 2
    assert not log.exists()
    assert "not valid JSON" in capsys.readouterr().err


def test_main_validate_flag_writes_nothing(tmp_path):
    log = tmp_path / "assay-runs.jsonl"
    src = tmp_path / "rec.json"
    src.write_text(json.dumps(minimal()))

    assert record_mod.main(["--file", str(src), "--log", str(log), "--validate"]) == 0
    assert not log.exists()


def test_main_writes_valid_record(tmp_path):
    log = tmp_path / "assay-runs.jsonl"
    src = tmp_path / "rec.json"
    src.write_text(json.dumps(minimal(run_id="r9")))

    assert record_mod.main(["--file", str(src), "--log", str(log)]) == 0
    assert json.loads(log.read_text().strip())["run_id"] == "r9"


# --- stats reader -------------------------------------------------------------


def write_log(tmp_path: Path, records: list[dict]) -> Path:
    log = tmp_path / "assay-runs.jsonl"
    with log.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(record_mod.validate(rec)) + "\n")
    return log


def test_missing_log_reports_zero_runs_not_an_error(tmp_path):
    records, warnings = stats_mod.load(tmp_path / "absent.jsonl")
    assert records == []
    assert any("no run log" in w for w in warnings)
    assert stats_mod.build_report(records)["runs"] == 0


def test_malformed_line_skipped_and_warned(tmp_path):
    log = tmp_path / "assay-runs.jsonl"
    log.write_text(json.dumps(record_mod.validate(minimal())) + "\n{broken\n")

    records, warnings = stats_mod.load(log)
    assert len(records) == 1
    assert any("line 2" in w for w in warnings)


def test_since_filter_excludes_older_runs(tmp_path):
    log = write_log(
        tmp_path,
        [
            minimal(run_id="old", ts="2026-01-01T00:00:00Z"),
            minimal(run_id="new", ts="2026-07-01T00:00:00Z"),
        ],
    )
    records, _ = stats_mod.load(log, since="2026-06-01")
    assert [r["run_id"] for r in records] == ["new"]


def test_stage_fire_rate_counts_eligible_denominator(tmp_path):
    log = write_log(
        tmp_path,
        [
            minimal(stages_eligible=["judge-panel"], stages_fired=["judge-panel"]),
            minimal(stages_eligible=["judge-panel"], stages_fired=[]),
        ],
    )
    records, _ = stats_mod.load(log)
    rates = stats_mod.stage_fire_rates(records)
    assert rates["judge-panel"]["fired"] == 1
    assert rates["judge-panel"]["eligible"] == 2
    assert rates["judge-panel"]["rate"] == 0.5


def test_stage_fire_rate_withholds_verdict_below_min_n(tmp_path):
    log = write_log(tmp_path, [minimal(stages_eligible=["plan"], stages_fired=[])])
    records, _ = stats_mod.load(log)
    assert "insufficient data" in stats_mod.stage_fire_rates(records)["plan"]["verdict"]


def test_stage_fire_rate_flags_unreliable_stage_at_sufficient_n(tmp_path):
    runs = [minimal(stages_eligible=["judge-panel"], stages_fired=[]) for _ in range(6)]
    records, _ = stats_mod.load(write_log(tmp_path, runs))
    assert stats_mod.stage_fire_rates(records)["judge-panel"]["verdict"] == "not firing reliably"


def test_edit_after_review_detects_changed_diff(tmp_path):
    log = write_log(
        tmp_path,
        [
            minimal(
                stages_fired=["judge-panel"],
                diff_before_review={"files": 1, "added": 10, "deleted": 0},
                diff_after_review={"files": 1, "added": 14, "deleted": 0},
            ),
            minimal(
                stages_fired=["judge-panel"],
                diff_before_review={"files": 1, "added": 10, "deleted": 0},
                diff_after_review={"files": 1, "added": 10, "deleted": 0},
            ),
        ],
    )
    records, _ = stats_mod.load(log)
    ear = stats_mod.edit_after_review(records)
    assert (ear["changed"], ear["judged"], ear["rate"]) == (1, 2, 0.5)


def test_edit_after_review_ignores_unjudged_and_incomplete_runs(tmp_path):
    log = write_log(
        tmp_path,
        [
            minimal(stages_fired=[]),  # panel never ran
            minimal(  # panel ran but no after-snapshot
                stages_fired=["judge-panel"],
                diff_before_review={"files": 1, "added": 1, "deleted": 0},
            ),
        ],
    )
    records, _ = stats_mod.load(log)
    assert stats_mod.edit_after_review(records)["judged"] == 0


def test_judge_acceptance_aggregates_across_runs(tmp_path):
    log = write_log(
        tmp_path,
        [
            minimal(
                judges=[{"judge": "security", "concerns": 4, "accepted": 3, "verdict": "block"}]
            ),
            minimal(judges=[{"judge": "security", "concerns": 6, "accepted": 2}]),
            minimal(judges=[{"judge": "naming", "concerns": 10, "accepted": 0}]),
        ],
    )
    records, _ = stats_mod.load(log)
    acc = stats_mod.judge_acceptance(records)

    assert acc["security"]["concerns"] == 10
    assert acc["security"]["accepted"] == 5
    assert acc["security"]["blocks"] == 1
    assert acc["security"]["verdict"] == "ok"
    assert acc["naming"]["verdict"] == "noise — consider cutting"


def test_judge_acceptance_withholds_verdict_below_min_concerns(tmp_path):
    log = write_log(tmp_path, [minimal(judges=[{"judge": "naming", "concerns": 2, "accepted": 0}])])
    records, _ = stats_mod.load(log)
    assert "insufficient data" in stats_mod.judge_acceptance(records)["naming"]["verdict"]


def test_approval_excludes_unknown_verdicts_from_denominator(tmp_path):
    log = write_log(
        tmp_path,
        [
            minimal(brandon_verdict="approved_first_pass"),
            minimal(brandon_verdict="approved_after_rework"),
            minimal(),  # unknown — must not count either way
        ],
    )
    records, _ = stats_mod.load(log)
    ap = stats_mod.approval(records)
    assert (ap["n"], ap["first_pass"], ap["rate"]) == (2, 1, 0.5)


def test_approval_reports_insufficient_data_and_medians(tmp_path):
    log = write_log(
        tmp_path,
        [
            minimal(brandon_verdict="approved_first_pass", rework_turns=0, tokens_total=100),
            minimal(brandon_verdict="abandoned", rework_turns=4, tokens_total=300),
        ],
    )
    records, _ = stats_mod.load(log)
    ap = stats_mod.approval(records)
    assert ap["insufficient_data"] is True
    assert ap["abandoned"] == 1
    assert ap["median_rework_turns"] == 2
    assert ap["median_tokens"] == 200


def test_render_handles_empty_log_without_crashing():
    assert "No runs recorded" in stats_mod.render(stats_mod.build_report([]), [])


def test_render_produces_all_four_sections(tmp_path):
    log = write_log(
        tmp_path,
        [
            minimal(
                stages_eligible=["judge-panel"],
                stages_fired=["judge-panel"],
                judges=[{"judge": "security", "concerns": 2, "accepted": 1}],
                diff_before_review={"files": 1, "added": 5, "deleted": 0},
                diff_after_review={"files": 1, "added": 7, "deleted": 0},
                brandon_verdict="approved_after_rework",
                rework_turns=1,
            )
        ],
    )
    records, warnings = stats_mod.load(log)
    out = stats_mod.render(stats_mod.build_report(records), warnings)
    for heading in ("STAGE FIRE RATE", "EDIT AFTER REVIEW", "JUDGE ACCEPTANCE", "APPROVAL"):
        assert heading in out


def test_stats_main_json_mode(tmp_path, capsys):
    log = write_log(tmp_path, [minimal()])
    assert stats_mod.main(["--log", str(log), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report"]["runs"] == 1
