"""Generate browser result data and an explicitly allowlisted code archive."""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = ["analysis.py", "plot_results.py", "README.md", "LICENSE",
         "EVALUATION.md", "data/results.json", "tests/test_analysis.py"]


def main():
    data = json.loads((ROOT / "code/data/results.json").read_text())
    (ROOT / "assets/results.js").write_text(
        "// Generated from code/data/results.json.\nwindow.FABRIC_RESULTS = "
        + json.dumps(data, separators=(",", ":")) + ";\n"
    )
    destination = ROOT / "assets/downloads/vla-fabric-tools.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for relative in FILES:
            archive.write(ROOT / "code" / relative, relative)
    print(f"Bundled {len(FILES)} files; browser result data refreshed.")


if __name__ == "__main__":
    main()
