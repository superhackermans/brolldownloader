"""
rareliquid B-Roll Bot -- Main entry point.
Runs the full pipeline with quality-gated iteration.
"""
import asyncio
import argparse
import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MAX_ITERATIONS
from steps.step1_entity_extraction import extract_entities
from steps.step2_youtube_search import search_for_entities
from steps.step3_transcript_analysis import analyze_transcripts
from steps.step4_image_search import search_and_download_images
from steps.step5_annotation import annotate_script
from steps.step6_custom_visuals import generate_custom_visuals
from steps.step7_quality_eval import evaluate_quality, get_retry_steps
from steps.step8_html_guide import generate_html_guide
from utils.formatters import timestamp_to_seconds


async def run_pipeline(script_path: str, output_dir: str):
    """Run the full B-roll research pipeline with iteration."""
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "pictures")
    videos_dir = os.path.join(output_dir, "videos")
    visuals_dir = os.path.join(output_dir, "custom_visuals")
    os.makedirs(videos_dir, exist_ok=True)

    with open(script_path) as f:
        script_text = f.read()

    print(f"Script loaded: {len(script_text)} chars, {len(script_text.split())} words")
    print(f"Estimated duration: {len(script_text.split()) / 150:.1f} minutes")
    print()

    all_broll_candidates = []
    all_image_assets = []
    all_custom_visuals = []
    entities = []
    assignment_map = []
    steps_to_retry = []
    annotated = ""
    report = {}
    new_sources = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"{'='*60}")
        print(f"ITERATION {iteration}/{MAX_ITERATIONS}")
        print(f"{'='*60}")
        start_time = time.time()

        # Step 1: Entity Extraction (only first iteration)
        if iteration == 1:
            print("\n[Step 1] Extracting entities...")
            entities = extract_entities(script_text)
            print(f"  Found {len(entities)} entities")
            for e in entities:
                print(f"    {e.type:10s} | {e.name} (era: {e.era})")

        # Step 2: YouTube Search
        if iteration == 1 or "step2" in steps_to_retry:
            print("\n[Step 2] Searching YouTube...")
            new_sources = await search_for_entities(entities)
            print(f"  Found {len(new_sources)} video sources with transcripts")

        # Step 3: Transcript Analysis
        if iteration == 1 or "step3" in steps_to_retry:
            print("\n[Step 3] Analyzing transcripts...")
            new_candidates = await analyze_transcripts(new_sources, entities)
            all_broll_candidates.extend(new_candidates)
            seen = set()
            deduped = []
            for c in all_broll_candidates:
                key = (c.url, c.start_time, c.end_time)
                if key not in seen:
                    seen.add(key)
                    deduped.append(c)
            all_broll_candidates = deduped
            print(f"  Total B-roll candidates: {len(all_broll_candidates)}")

        # Step 4: Image Search
        if iteration == 1 or "step4" in steps_to_retry:
            print("\n[Step 4] Searching for images...")
            new_images = await search_and_download_images(
                entities, images_dir, start_index=len(all_image_assets) + 1
            )
            all_image_assets.extend(new_images)
            print(f"  Total images: {len(all_image_assets)}")

        # Step 5: Script Annotation
        print("\n[Step 5] Annotating script...")
        annotated, assignment_map = annotate_script(script_text, all_broll_candidates, all_image_assets)

        # Step 6: Custom Visuals
        if iteration == 1:
            print("\n[Step 6] Generating custom visuals...")
            all_custom_visuals = generate_custom_visuals(annotated, visuals_dir)
            print(f"  Generated {len(all_custom_visuals)} custom visuals")

        # Step 7: Quality Evaluation
        print("\n[Step 7] Evaluating quality...")
        report = evaluate_quality(
            annotated, all_broll_candidates, all_image_assets,
            all_custom_visuals, script_text
        )

        elapsed = time.time() - start_time
        print(f"\n  Iteration {iteration} completed in {elapsed:.1f}s")
        print(f"\n  VERDICT: {report['verdict']}")
        print(f"  Metrics:")
        for k, v in report['metrics'].items():
            print(f"    {k}: {v}")

        if report['failures']:
            print(f"\n  FAILURES:")
            for f in report['failures']:
                print(f"    FAIL: {f['message']}")

        if report['warnings']:
            print(f"\n  WARNINGS:")
            for w in report['warnings']:
                print(f"    WARN: {w}")

        if report['verdict'] in ('PASS', 'PASS_WITH_WARNINGS'):
            print(f"\nQuality gate PASSED. Finalizing output.")
            break

        steps_to_retry = get_retry_steps(report)
        if not steps_to_retry or iteration == MAX_ITERATIONS:
            print(f"\nMax iterations reached or no retry steps identified.")
            break

        print(f"\n  Retrying steps: {steps_to_retry}")

        if "step2" in steps_to_retry or "step3" in steps_to_retry:
            for entity in entities:
                entity.youtube_queries.append(f"{entity.name} explained")
                entity.youtube_queries.append(f"{entity.name} overview")

        if "step4" in steps_to_retry:
            for entity in entities:
                entity.image_queries.append(f"{entity.name} photo")
                entity.image_queries.append(f"{entity.name} news")

    # ── Save outputs ──────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("SAVING OUTPUTS")
    print(f"{'='*60}")

    # Annotated script
    annotated_path = os.path.join(output_dir, "annotated_script.md")
    with open(annotated_path, 'w') as f:
        f.write(annotated)
    print(f"  Annotated script: {annotated_path}")

    # Quality report
    report_path = os.path.join(output_dir, "quality_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Quality report: {report_path}")

    # Videos folder -- B-roll manifest
    broll_manifest = {
        "description": "B-roll video cache manifest. Each entry is a clip the editor can pull from YouTube.",
        "total_clips": len(all_broll_candidates),
        "unique_sources": len(set(c.url for c in all_broll_candidates)),
        "clips": [
            {
                "url": c.url,
                "url_at_timestamp": f"{c.url}&t={timestamp_to_seconds(c.start_time)}",
                "video_title": c.video_title,
                "channel": c.channel,
                "start_time": c.start_time,
                "end_time": c.end_time,
                "duration_seconds": timestamp_to_seconds(c.end_time) - timestamp_to_seconds(c.start_time),
                "entity": c.entity_name,
                "description": c.description,
                "relevance_score": c.relevance_score,
                "era_appropriate": c.era_appropriate,
                "with_audio": c.with_audio,
                "source_type": c.source_type,
                "transcript_excerpt": c.transcript_excerpt,
                "match_reasoning": c.match_reasoning
            }
            for c in sorted(all_broll_candidates, key=lambda x: -x.relevance_score)
        ]
    }
    manifest_path = os.path.join(videos_dir, "broll_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(broll_manifest, f, indent=2)
    print(f"  B-roll manifest: {manifest_path}")

    # Asset inventory
    inventory = {
        "broll_candidates": [
            {
                "url": c.url, "start": c.start_time, "end": c.end_time,
                "entity": c.entity_name, "relevance": c.relevance_score,
                "description": c.description, "with_audio": c.with_audio,
                "era_ok": c.era_appropriate, "source_type": c.source_type,
                "transcript_excerpt": c.transcript_excerpt,
                "match_reasoning": c.match_reasoning
            }
            for c in all_broll_candidates
        ],
        "images": [
            {
                "filename": img.filename, "entity": img.entity_name,
                "type": img.type, "source_url": img.source_url,
                "description": img.description,
                "match_reasoning": img.match_reasoning
            }
            for img in all_image_assets
        ],
        "custom_visuals": all_custom_visuals
    }
    inventory_path = os.path.join(output_dir, "asset_inventory.json")
    with open(inventory_path, 'w') as f:
        json.dump(inventory, f, indent=2)
    print(f"  Asset inventory: {inventory_path}")

    # Step 8: Interactive HTML Editing Guide
    print(f"\n[Step 8] Generating interactive HTML editing guide...")
    guide_path = os.path.join(output_dir, "editing_guide.html")
    generate_html_guide(
        script_text=script_text,
        assignment_map=assignment_map,
        broll_candidates=all_broll_candidates,
        image_assets=all_image_assets,
        custom_visuals=all_custom_visuals,
        quality_report=report,
        output_path=guide_path,
        images_dir=images_dir
    )
    print(f"  Editing guide: {guide_path}")

    print(f"\n  Pictures folder: {images_dir}/ ({len(all_image_assets)} files)")
    print(f"  Videos folder: {videos_dir}/ (manifest with {len(all_broll_candidates)} clips)")
    print(f"  Custom visuals: {visuals_dir}/ ({len(all_custom_visuals)} files)")
    print(f"\n{'='*60}")
    print(f"DONE. Final verdict: {report['verdict']}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="rareliquid B-Roll Research Bot")
    parser.add_argument("--script", required=True, help="Path to script file (.txt or .md)")
    parser.add_argument("--output", default="./output", help="Output directory")
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.script, args.output))


if __name__ == "__main__":
    main()
