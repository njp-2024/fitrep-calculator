"""
eval_split.py

Sampling and packet preparation for Part B (scaled prompts) human evaluation.

Splits 180 Part B outputs (9 models x 20 cases) into human-eval and LLM-eval
sets, then formats the human set into survey packets for evaluators.

Run from project root with:
  python -m experiments.prelim_benchmark.eval_split \
      --run-dir outputs/runs/YYYYMMDD_scaled \
      --seed 42
"""

import argparse
import csv
import json
import random
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


# -- Data loading ------------------------------------------------------------

def load_results(run_dir: Path) -> list[dict]:
    """
    Load Part B results from a completed run directory.
    Filters out error entries and validates evaluation IDs exist.
    """
    results_path = run_dir / "results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"No results.json found in {run_dir}")

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter to successful results only
    results = []
    skipped = 0
    for entry in data["results"]:
        if entry.get("error") is not None:
            skipped += 1
            continue
        if not entry.get("evaluation_id"):
            skipped += 1
            continue
        results.append(entry)

    print(f"Loaded {len(results)} successful results ({skipped} skipped)")
    return results


# -- Stratified sampling ----------------------------------------------------

def stratified_sample(
    results: list[dict],
    seed: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Stratified random sampling: 1 sample per (model_name, target_tier) cell
    per wave, for 2 waves.

    Returns:
        (wave1_samples, wave2_samples, llm_remainder)
        - wave1_samples: 36 items (1 per cell)
        - wave2_samples: 36 items (1 per cell, different from wave 1)
        - llm_remainder: remaining items (180 - 72 = 108)
    """
    rng = random.Random(seed)

    # Group by (model_name, target_tier)
    cells = defaultdict(list)
    for r in results:
        key = (r["model_name"], r["target_tier"])
        cells[key].append(r)

    wave1 = []
    wave2 = []
    remainder = []

    for key in sorted(cells.keys()):
        group = cells[key]
        rng.shuffle(group)

        if len(group) >= 2:
            wave1.append(group[0])
            wave2.append(group[1])
            remainder.extend(group[2:])
        elif len(group) == 1:
            # Only 1 available — assign to wave 1, nothing for wave 2
            wave1.append(group[0])
        # Empty groups are skipped

    print(f"Stratified sample: {len(wave1)} wave 1, {len(wave2)} wave 2, "
          f"{len(remainder)} remainder")

    return wave1, wave2, remainder


# -- Calibration selection ---------------------------------------------------

def select_calibration(
    wave1_samples: list[dict],
    n: int,
    seed: int,
) -> list[dict]:
    """
    Select ~n calibration samples from wave 1 for human+LLM dual evaluation.
    Tries to balance across tiers.
    """
    rng = random.Random(seed + 1)  # offset seed for independent randomness

    # Group wave 1 samples by tier
    by_tier = defaultdict(list)
    for s in wave1_samples:
        by_tier[s["target_tier"]].append(s)

    # Pick roughly n/num_tiers per tier, rounding up where needed
    tiers = sorted(by_tier.keys())
    per_tier = max(1, n // len(tiers))
    calibration = []

    for tier in tiers:
        pool = by_tier[tier][:]
        rng.shuffle(pool)
        take = min(per_tier, len(pool))
        calibration.extend(pool[:take])

    # If under target, fill from remaining wave 1 samples
    if len(calibration) < n:
        already = {s["evaluation_id"] for s in calibration}
        extras = [s for s in wave1_samples if s["evaluation_id"] not in already]
        rng.shuffle(extras)
        calibration.extend(extras[: n - len(calibration)])

    print(f"Calibration set: {len(calibration)} samples")
    return calibration


# -- Packet construction -----------------------------------------------------

def build_packets(
    samples: list[dict],
    num_packets: int,
    packet_size: int,
    seed: int,
) -> list[list[dict]]:
    """
    Build packets via circular rotation over a tier-interleaved list.

    Algorithm:
    1. Sort samples into a tier-interleaved list (cycle through tiers)
    2. For packet i: take circular slice of packet_size starting at
       offset (i * len(samples) // num_packets) % len(samples)
    3. Shuffle within each packet for presentation order

    Guarantees:
    - Approximately packet_size/num_tiers narratives per tier per packet
      (exact when packet_size is divisible by num_tiers)
    - Each sample appears in exactly num_packets * packet_size / len(samples) packets
    """
    rng = random.Random(seed + 2)

    # Group by tier, sort within each group for determinism
    by_tier = defaultdict(list)
    for s in samples:
        by_tier[s["target_tier"]].append(s)

    tiers = sorted(by_tier.keys())
    for tier in tiers:
        by_tier[tier].sort(key=lambda x: x["evaluation_id"])

    # Interleave: cycle through tiers, pulling one at a time
    interleaved = []
    max_per_tier = max(len(by_tier[t]) for t in tiers) if tiers else 0
    for i in range(max_per_tier):
        for tier in tiers:
            if i < len(by_tier[tier]):
                interleaved.append(by_tier[tier][i])

    n = len(interleaved)
    if n == 0:
        return []

    packets = []

    for i in range(num_packets):
        offset = (i * n // num_packets) % n
        packet = []
        for j in range(min(packet_size, n)):
            idx = (offset + j) % n
            packet.append(interleaved[idx])
        rng.shuffle(packet)
        packets.append(packet)

    return packets


# -- Export functions --------------------------------------------------------

def _clean_narrative(text: str) -> str:
    """Strip reasoning chain-of-thought tags from generated text."""
    return re.sub(r"<think>[\s\S]*?</think>", "", text).strip()


def export_packets(
    packets: list[list[dict]],
    wave: int,
    output_dir: Path,
) -> None:
    """Write each packet as a plain .txt file for survey distribution."""
    wave_dir = output_dir / "human_eval" / f"wave{wave}"
    wave_dir.mkdir(parents=True, exist_ok=True)

    for idx, packet in enumerate(packets, start=1):
        filename = f"wave{wave}_packet_{idx:02d}.txt"
        filepath = wave_dir / filename

        lines = []
        lines.append(f"=== Evaluation Packet {idx:02d} ===")
        lines.append(f"Evaluator: _______________")
        lines.append(f"Date: _______________")
        lines.append("")

        for n_idx, sample in enumerate(packet, start=1):
            narrative = _clean_narrative(sample["generated_text"])
            accomplishments = sample.get("_accomplishments", "N/A")
            lines.append(f"--- Narrative {n_idx} of {len(packet)} ---")
            lines.append(f"Evaluation ID: {sample['evaluation_id']}")
            lines.append(f"Rank: {sample.get('_rank', 'N/A')}")
            lines.append(f"Name: {sample.get('_name', 'N/A')}")
            lines.append(f"Billet: {sample.get('_billet', 'N/A')}")
            lines.append(f"Target Tier: {sample['target_tier']}")
            lines.append("")
            lines.append("Accomplishments:")
            lines.append(accomplishments)
            lines.append("")
            lines.append("Generated Narrative:")
            lines.append(narrative)
            lines.append("")
            lines.append("Your Rating: ___")
            lines.append("Comments: _______________")
            lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    print(f"  Wrote {len(packets)} packets to {wave_dir}")


def export_llm_csv(
    items: list[dict],
    filename: str,
    output_dir: Path,
) -> None:
    """Write LLM evaluation set as CSV."""
    llm_dir = output_dir / "llm_eval"
    llm_dir.mkdir(parents=True, exist_ok=True)
    filepath = llm_dir / filename

    fieldnames = [
        "evaluation_id", "case_id", "model_name", "target_tier",
        "generated_text", "char_count",
    ]

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({
                "evaluation_id": item["evaluation_id"],
                "case_id": item["case_id"],
                "model_name": item["model_name"],
                "target_tier": item["target_tier"],
                "generated_text": _clean_narrative(item["generated_text"]),
                "char_count": item["char_count"],
            })

    print(f"  Wrote {len(items)} rows to {filepath}")


def export_calibration(
    calibration: list[dict],
    output_dir: Path,
) -> None:
    """Write calibration set CSV (samples that get both human + LLM eval)."""
    cal_dir = output_dir / "calibration"
    cal_dir.mkdir(parents=True, exist_ok=True)
    filepath = cal_dir / "calibration_set.csv"

    fieldnames = [
        "evaluation_id", "case_id", "model_name", "target_tier",
        "generated_text", "char_count",
    ]

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in calibration:
            writer.writerow({
                "evaluation_id": item["evaluation_id"],
                "case_id": item["case_id"],
                "model_name": item["model_name"],
                "target_tier": item["target_tier"],
                "generated_text": _clean_narrative(item["generated_text"]),
                "char_count": item["char_count"],
            })

    print(f"  Wrote {len(calibration)} calibration rows to {filepath}")


def export_assignments(
    wave1_samples: list[dict],
    wave1_packets: list[list[dict]],
    wave2_samples: list[dict],
    wave2_packets: list[list[dict]],
    output_dir: Path,
) -> None:
    """
    Write master assignment CSV linking evaluation IDs to waves,
    packets, and models (for post-analysis unblinding).
    """
    human_dir = output_dir / "human_eval"
    human_dir.mkdir(parents=True, exist_ok=True)
    filepath = human_dir / "sample_assignments.csv"

    # Build packet membership lookup
    def build_packet_map(packets, wave):
        mapping = defaultdict(list)
        for pkt_idx, packet in enumerate(packets, start=1):
            for sample in packet:
                mapping[sample["evaluation_id"]].append(
                    f"wave{wave}_packet_{pkt_idx:02d}"
                )
        return mapping

    w1_map = build_packet_map(wave1_packets, 1)
    w2_map = build_packet_map(wave2_packets, 2)

    fieldnames = [
        "evaluation_id", "wave", "case_id", "model_name",
        "target_tier", "packet_ids",
    ]
    rows = []

    for s in wave1_samples:
        eid = s["evaluation_id"]
        rows.append({
            "evaluation_id": eid,
            "wave": 1,
            "case_id": s["case_id"],
            "model_name": s["model_name"],
            "target_tier": s["target_tier"],
            "packet_ids": "; ".join(w1_map.get(eid, [])),
        })

    for s in wave2_samples:
        eid = s["evaluation_id"]
        rows.append({
            "evaluation_id": eid,
            "wave": 2,
            "case_id": s["case_id"],
            "model_name": s["model_name"],
            "target_tier": s["target_tier"],
            "packet_ids": "; ".join(w2_map.get(eid, [])),
        })

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows)} assignment rows to {filepath}")


def export_summary(
    wave1_samples: list[dict],
    wave1_packets: list[list[dict]],
    wave2_samples: list[dict],
    wave2_packets: list[list[dict]],
    calibration: list[dict],
    output_dir: Path,
) -> None:
    """Write human-readable summary of the eval split."""
    filepath = output_dir / "summary.txt"

    lines = []
    lines.append("=" * 60)
    lines.append("EVALUATION SPLIT SUMMARY")
    lines.append("=" * 60)
    lines.append("")

    # Overview
    total_human = len(wave1_samples) + len(wave2_samples)
    lines.append(f"Total human-eval samples: {total_human}")
    lines.append(f"  Wave 1: {len(wave1_samples)} samples -> "
                 f"{len(wave1_packets)} packets")
    lines.append(f"  Wave 2: {len(wave2_samples)} samples -> "
                 f"{len(wave2_packets)} packets")
    lines.append(f"Calibration (dual human+LLM): {len(calibration)} samples")
    lines.append("")

    # Wave details
    for wave_num, samples, packets in [
        (1, wave1_samples, wave1_packets),
        (2, wave2_samples, wave2_packets),
    ]:
        lines.append("-" * 60)
        lines.append(f"WAVE {wave_num}")
        lines.append("-" * 60)
        lines.append("")

        # Tier distribution
        tier_counts = defaultdict(int)
        model_counts = defaultdict(int)
        for s in samples:
            tier_counts[s["target_tier"]] += 1
            model_counts[s["model_name"]] += 1

        lines.append("Tier distribution:")
        for tier in sorted(tier_counts.keys()):
            lines.append(f"  {tier}: {tier_counts[tier]}")
        lines.append("")

        lines.append("Model distribution:")
        for model in sorted(model_counts.keys()):
            lines.append(f"  {model}: {model_counts[model]}")
        lines.append("")

        # Packet contents
        lines.append("Packet contents:")
        for pkt_idx, packet in enumerate(packets, start=1):
            eids = [s["evaluation_id"] for s in packet]
            tiers = [s["target_tier"] for s in packet]
            tier_summary = defaultdict(int)
            for t in tiers:
                tier_summary[t] += 1
            tier_str = ", ".join(
                f"{t}: {c}" for t, c in sorted(tier_summary.items())
            )
            lines.append(
                f"  Packet {pkt_idx:02d}: [{', '.join(eids)}] "
                f"({tier_str})"
            )
        lines.append("")

        # Sample appearance counts
        appearance = defaultdict(int)
        for packet in packets:
            for s in packet:
                appearance[s["evaluation_id"]] += 1
        counts = sorted(set(appearance.values()))
        lines.append("Sample appearances across packets:")
        for c in counts:
            n = sum(1 for v in appearance.values() if v == c)
            lines.append(f"  Appears {c}x: {n} samples")
        lines.append("")

    # Calibration
    lines.append("-" * 60)
    lines.append("CALIBRATION SET")
    lines.append("-" * 60)
    for s in calibration:
        lines.append(
            f"  {s['evaluation_id']} | {s['model_name']} | {s['target_tier']}"
        )
    lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Wrote summary to {filepath}")


def export_manifest(
    args: argparse.Namespace,
    wave1_samples: list[dict],
    wave2_samples: list[dict],
    calibration: list[dict],
    llm_remainder: list[dict],
    output_dir: Path,
) -> None:
    """Write manifest.json with split parameters and counts."""
    filepath = output_dir / "manifest.json"

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(args.run_dir),
        "seed": args.seed,
        "packet_size": 9,
        "num_packets_per_wave": 12,
        "counts": {
            "wave1_human_eval": len(wave1_samples),
            "wave2_human_eval": len(wave2_samples),
            "total_human_eval": len(wave1_samples) + len(wave2_samples),
            "calibration": len(calibration),
            "llm_eval_wave1_only": len(llm_remainder) + len(wave2_samples),
            "llm_eval_both_waves": len(llm_remainder),
        },
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"  Wrote manifest to {filepath}")


# -- Case data enrichment ---------------------------------------------------

def enrich_with_case_data(samples: list[dict], run_dir: Path) -> None:
    """
    Join case data (rank, name, billet, accomplishments) onto sample dicts.
    Loads from the dataset file used in the original run.
    """
    # Load dataset from the run's data directory
    data_dir = Path(__file__).parent / "data"
    manifest_path = run_dir / "manifest.json"

    # Try to determine which dataset was used from the run manifest
    dataset_file = "synthetic_cases_v1.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        # The run manifest doesn't store dataset filename, use default
        # (dataset_version is available but filename mapping is 1:1)

    dataset_path = data_dir / dataset_file
    if not dataset_path.exists():
        print(f"  WARNING: Dataset {dataset_path} not found, skipping enrichment")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    case_lookup = {}
    for case in raw["cases"]:
        case_lookup[case["case_id"]] = case

    for s in samples:
        case = case_lookup.get(s["case_id"])
        if case:
            s["_rank"] = case["rank"]
            s["_name"] = case["name"]
            s["_billet"] = case["billet_title"]
            accomplishments = case["accomplishments"]
            s["_accomplishments"] = "\n".join(
                f"- {a}" for a in accomplishments
            )


# -- CLI and main ------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Split Part B benchmark outputs into human-eval and "
                    "LLM-eval sets, and build survey packets.",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Path to a completed Part B run directory (containing results.json). "
             "Relative paths are resolved from experiments/prelim_benchmark/.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolve run directory relative to experiment root if needed
    if not args.run_dir.is_absolute():
        args.run_dir = Path(__file__).parent / args.run_dir

    print("=== Evaluation Split & Packet Builder ===")
    print(f"Run directory: {args.run_dir}")
    print(f"Seed: {args.seed}")
    print()

    # 1. Load Part B results
    results = load_results(args.run_dir)

    # 2. Stratified sample — both waves at once
    wave1_samples, wave2_samples, llm_remainder = stratified_sample(
        results, seed=args.seed,
    )

    # 3. Select calibration subset (from wave 1)
    calibration = select_calibration(wave1_samples, n=10, seed=args.seed)

    # 4. Enrich samples with case data for packet display
    all_human = wave1_samples + wave2_samples
    enrich_with_case_data(all_human, args.run_dir)

    # 5. Build 12 packets per wave via circular rotation
    wave1_packets = build_packets(
        wave1_samples, num_packets=12, packet_size=9, seed=args.seed,
    )
    wave2_packets = build_packets(
        wave2_samples, num_packets=12, packet_size=9, seed=args.seed,
    )

    # 6. Create output directory
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "outputs" / f"eval_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")
    print()

    # 7. Export everything
    print("Exporting...")

    # LLM eval CSVs
    export_llm_csv(
        llm_remainder + wave2_samples,
        "llm_set_wave1_only.csv",
        output_dir,
    )
    export_llm_csv(
        llm_remainder,
        "llm_set_both_waves.csv",
        output_dir,
    )

    # Human eval packets
    export_packets(wave1_packets, wave=1, output_dir=output_dir)
    export_packets(wave2_packets, wave=2, output_dir=output_dir)

    # Calibration
    export_calibration(calibration, output_dir)

    # Assignments and summary
    export_assignments(
        wave1_samples, wave1_packets,
        wave2_samples, wave2_packets,
        output_dir,
    )
    export_summary(
        wave1_samples, wave1_packets,
        wave2_samples, wave2_packets,
        calibration,
        output_dir,
    )
    export_manifest(
        args, wave1_samples, wave2_samples,
        calibration, llm_remainder, output_dir,
    )

    print()
    print("Done.")
    print(f"Results in: {output_dir}")


if __name__ == "__main__":
    main()
