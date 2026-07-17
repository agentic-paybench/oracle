"""MockBench CLI.

    python -m paybench.mockbench.cli generate   # gen fixtures + write provenance hashes
    python -m paybench.mockbench.cli run         # run the 5,000-trial finality benchmark
    python -m paybench.mockbench.cli verify       # re-verify fixture hashes vs provenance
    python -m paybench.mockbench.cli all          # generate then run
"""

from __future__ import annotations

import argparse
import re
import sys

from . import K_GRID_SECONDS, SETTLING_RAILS
from .fixtures import generate_fixture, load_fixture
from .bench import run_benchmark, write_report
from .paths import provenance_path


def cmd_generate(_: argparse.Namespace) -> int:
    print("Generating calibrated log-normal finality fixtures (seeded)...\n")
    for rail in SETTLING_RAILS:
        gf = generate_fixture(rail)
        flag = "updated" if gf.provenance_updated else "unchanged"
        print(
            f"  {rail:<4} median={gf.median_s:<6} sigma_log={gf.sigma_log:<6} "
            f"n={gf.n_samples}  {gf.hash}  (provenance {flag})"
        )
    print("\nDone. Provenance fixture_content_hash fields written.")
    return 0


def cmd_verify(_: argparse.Namespace) -> int:
    ok = True
    hash_re = re.compile(r'fixture_content_hash:\s*"(.*?)"')
    for rail in SETTLING_RAILS:
        try:
            obj = load_fixture(rail)  # raises on hash mismatch
        except (FileNotFoundError, ValueError) as exc:
            print(f"  {rail:<4} FAIL  {exc}")
            ok = False
            continue
        prov_text = provenance_path(rail).read_text(encoding="utf-8")
        m = hash_re.search(prov_text)
        prov_hash = m.group(1) if m else ""
        match = prov_hash == obj["content_hash"]
        ok = ok and match
        status = "OK  " if match else "FAIL"
        print(f"  {rail:<4} {status} fixture={obj['content_hash']}  provenance={'match' if match else prov_hash or '(empty)'}")
    print("\nAll fixtures verified." if ok else "\nVERIFICATION FAILED.")
    return 0 if ok else 1


def cmd_run(_: argparse.Namespace) -> int:
    report = run_benchmark()
    path = write_report(report)
    cfg = report["config"]
    bt = report["bradley_terry"]

    print("PayBench — settlement-finality benchmark")
    print(
        f"  {cfg['n_pairs']} pairs x {cfg['trials_per_pair']} trials "
        f"= {cfg['total_trials']} trials   seed={cfg['master_seed']}"
    )
    print(f"  run_hash {report['run_hash']}\n")

    print("Bradley-Terry strength (fastest-settling first):")
    for rank, rail in enumerate(bt["ranking"], 1):
        name = cfg["rail_names"][rail]
        print(f"  {rank}. {rail:<4} {bt['strengths'][rail]:.4f}  {name}")
    print(f"  (converged={bt['converged']} in {bt['iterations']} iters)\n")

    print(f"pass@k = P(finality <= k s)  [Wilson 95% lower bound in brackets]")
    header = "  rail  " + "  ".join(f"k={k:<2}" for k in K_GRID_SECONDS)
    print(header)
    for rail in cfg["rails"]:
        cells = []
        for row in report["pass_at_k"][rail]:
            cells.append(f"{row['phat']:.2f}[{row['wilson_lb']:.2f}]")
        print(f"  {rail:<4}  " + "  ".join(cells))
    print(f"\nReport written: {path}")
    return 0


def cmd_all(ns: argparse.Namespace) -> int:
    rc = cmd_generate(ns)
    if rc != 0:
        return rc
    print()
    return cmd_run(ns)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="paybench-mockbench", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generate", help="generate fixtures + write provenance hashes").set_defaults(func=cmd_generate)
    sub.add_parser("verify", help="re-verify fixture hashes vs provenance").set_defaults(func=cmd_verify)
    sub.add_parser("run", help="run the settlement-finality benchmark").set_defaults(func=cmd_run)
    sub.add_parser("all", help="generate then run").set_defaults(func=cmd_all)
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
