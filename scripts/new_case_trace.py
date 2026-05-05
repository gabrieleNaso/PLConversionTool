from __future__ import annotations

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a per-case trace markdown stub under cases/traces/.")
    parser.add_argument("--n", type=int, required=True, help="Case number N (creates inputN_expected_outputN.md).")
    args = parser.parse_args()

    n = int(args.n)
    if n <= 0:
        raise SystemExit("--n must be >= 1")

    trace_dir = PROJECT_ROOT / "cases" / "traces"
    trace_dir.mkdir(parents=True, exist_ok=True)

    trace_path = trace_dir / f"input{n}_expected_output{n}.md"
    if trace_path.exists():
        raise SystemExit(f"Trace already exists: {trace_path.relative_to(PROJECT_ROOT)}")

    trace_path.write_text(
        "\n".join(
            [
                f"# Trace: input{n} vs expected_output{n}",
                "",
                "Questo file documenta come il caso deve essere tradotto (AWL -> bundle XML TIA).",
                "",
                "## Sorgenti",
                "",
                "- Input (AWL):",
                f"  - `cases/input/input{n}/`",
                "- Expected output (assoluto):",
                f"  - `cases/expected_output/expected_output{n}/`",
                "",
                "## Obiettivo del caso",
                "",
                "- (compilare)",
                "",
                "## Inventario expected",
                "",
                "- FB GRAPH:",
                "- FC famiglie:",
                "- DB:",
                "",
                "## Regole di traduzione da fissare",
                "",
                "- (compilare)",
                "",
                "## Criteri di confronto",
                "",
                "- Naming blocchi",
                "- Topologia GRAPH",
                "- Logica FC",
                "- Struttura DB",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {trace_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

