"""
Quality Evaluation -- Check output against quality thresholds.
"""
import re
import json
from config import QUALITY_THRESHOLDS


def evaluate_quality(
    annotated_script: str,
    broll_candidates: list,
    image_assets: list,
    custom_visuals: list,
    script_text: str
) -> dict:
    """Evaluate the quality of the bot's output."""
    total_lines = len([l for l in script_text.strip().split('\n') if l.strip()])

    broll_refs = re.findall(r'\[https://www\.youtube\.com/watch\?v=([^,\]]+)', annotated_script)
    pic_refs = re.findall(r'\[pic (\d+)', annotated_script)
    audio_refs = re.findall(r'WITH AUDIO', annotated_script)
    gaps = re.findall(r'\[NO B-ROLL FOUND', annotated_script)
    custom_flags = re.findall(r'\[CUSTOM VISUAL NEEDED', annotated_script)

    unique_broll = len(set(broll_refs))
    unique_images = len(set(pic_refs))
    total_broll_placements = len(broll_refs)
    total_image_placements = len(pic_refs)

    lines_with_visual = 0
    for line in annotated_script.split('\n'):
        if '[https://' in line or '[pic ' in line or '[CUSTOM VISUAL' in line:
            lines_with_visual += 1

    coverage_pct = (lines_with_visual / max(total_lines, 1)) * 100
    gap_pct = (len(gaps) / max(total_lines, 1)) * 100

    word_count = len(script_text.split())
    estimated_duration_min = word_count / 150

    broll_per_min = unique_broll / max(estimated_duration_min, 1)
    images_per_min = unique_images / max(estimated_duration_min, 1)

    relevance_scores = [c.relevance_score for c in broll_candidates if c.relevance_score >= 5]
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

    era_mismatches = sum(1 for c in broll_candidates if not c.era_appropriate and c.relevance_score >= 6)

    stock_count = sum(1 for c in broll_candidates if c.source_type == "other")
    stock_pct = (stock_count / max(len(broll_candidates), 1)) * 100

    report = {
        "metrics": {
            "unique_broll_sources": unique_broll,
            "unique_still_images": unique_images,
            "total_broll_placements": total_broll_placements,
            "total_image_placements": total_image_placements,
            "broll_with_audio": len(audio_refs),
            "custom_visuals_generated": len(custom_visuals),
            "custom_visuals_flagged": len(custom_flags),
            "lines_with_no_visual": len(gaps),
            "coverage_percentage": round(coverage_pct, 1),
            "gap_percentage": round(gap_pct, 1),
            "estimated_script_duration_min": round(estimated_duration_min, 1),
            "broll_per_minute": round(broll_per_min, 1),
            "images_per_minute": round(images_per_min, 1),
            "avg_relevance_score": round(avg_relevance, 1),
            "era_mismatches": era_mismatches,
            "stock_footage_percentage": round(stock_pct, 1),
        },
        "checks": {},
        "failures": [],
        "warnings": [],
        "verdict": "PASS"
    }

    T = QUALITY_THRESHOLDS

    checks = [
        ("unique_broll_sources", unique_broll, ">=", T["min_broll_unique_sources"],
         f"Need {T['min_broll_unique_sources']} unique B-roll sources, have {unique_broll}",
         "step2_step3"),
        ("unique_still_images", unique_images, ">=", T["min_still_images"],
         f"Need {T['min_still_images']} unique images, have {unique_images}",
         "step4"),
        ("coverage_percentage", coverage_pct, ">=", T["min_coverage_percentage"],
         f"Need {T['min_coverage_percentage']}% coverage, have {coverage_pct:.1f}%",
         "step5"),
        ("gap_percentage", gap_pct, "<=", T["max_gap_percentage"],
         f"Gap percentage {gap_pct:.1f}% exceeds max {T['max_gap_percentage']}%",
         "step2_step3_step4"),
        ("avg_relevance_score", avg_relevance, ">=", T["min_avg_relevance_score"],
         f"Avg relevance {avg_relevance:.1f} below min {T['min_avg_relevance_score']}",
         "step3"),
        ("era_mismatches", era_mismatches, "<=", T["max_era_mismatch_count"],
         f"Found {era_mismatches} era mismatches (max: {T['max_era_mismatch_count']})",
         "step3"),
        ("broll_per_minute", broll_per_min, ">=", T["min_broll_per_minute"],
         f"B-roll/min: {broll_per_min:.1f} below min {T['min_broll_per_minute']}",
         "step2_step3"),
        ("images_per_minute", images_per_min, ">=", T["min_images_per_minute"],
         f"Images/min: {images_per_min:.1f} below min {T['min_images_per_minute']}",
         "step4"),
    ]

    for name, value, op, threshold, message, fix_step in checks:
        if op == ">=" and value < threshold:
            report["checks"][name] = "FAIL"
            report["failures"].append({"check": name, "message": message, "fix_step": fix_step})
        elif op == "<=" and value > threshold:
            report["checks"][name] = "FAIL"
            report["failures"].append({"check": name, "message": message, "fix_step": fix_step})
        else:
            report["checks"][name] = "PASS"

    if unique_broll < T["target_broll_unique_sources"] and unique_broll >= T["min_broll_unique_sources"]:
        report["warnings"].append(f"B-roll below target: {unique_broll} (target: {T['target_broll_unique_sources']})")
    if unique_images < T["target_still_images"] and unique_images >= T["min_still_images"]:
        report["warnings"].append(f"Images below target: {unique_images} (target: {T['target_still_images']})")
    if coverage_pct < T["target_coverage_percentage"] and coverage_pct >= T["min_coverage_percentage"]:
        report["warnings"].append(f"Coverage below target: {coverage_pct:.1f}% (target: {T['target_coverage_percentage']}%)")

    if report["failures"]:
        report["verdict"] = "FAIL"
    elif report["warnings"]:
        report["verdict"] = "PASS_WITH_WARNINGS"
    else:
        report["verdict"] = "PASS"

    return report


def get_retry_steps(report: dict) -> list[str]:
    """Determine which steps to re-run based on failures."""
    steps_to_retry = set()
    for failure in report["failures"]:
        for step in failure["fix_step"].split("_"):
            steps_to_retry.add(step)
    return sorted(steps_to_retry)
