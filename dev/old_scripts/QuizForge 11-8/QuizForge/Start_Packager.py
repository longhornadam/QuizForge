"""Batch packager runner for DropZone.

This helper sweeps all `.txt` specs dropped into the repo-level
`DropZone/` directory and invokes the QuizForge packager on each file.
Generated ZIPs land in `Processed/` alongside the originals.

Usage:
	python Start_Packager.py

The script can run from any working directory; paths are resolved
relative to the location of this file.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
	repo_root = Path(__file__).resolve().parent
	dropzone = repo_root / "DropZone"
	processed = repo_root / "Processed"
	packager_script = repo_root / "Packager" / "quizforge_packager.py"

	dropzone.mkdir(parents=True, exist_ok=True)
	processed.mkdir(parents=True, exist_ok=True)

	txt_files = sorted(dropzone.glob("*.txt"))

	if not txt_files:
		print("[INFO] No .txt files found in DropZone.")
		return 0

	if not packager_script.exists():
		print(f"[ERROR] Packager script not found: {packager_script}")
		return 1

	any_failure = False

	for spec_path in txt_files:
		output_zip = processed / f"{spec_path.stem}.zip"
		log_path = processed / f"{spec_path.stem}.log"

		print(f"[INFO] Packaging {spec_path.name} -> {output_zip.name}")

		result = subprocess.run(
			[
				sys.executable,
				str(packager_script),
				str(spec_path),
				"-o",
				str(output_zip),
			],
			capture_output=True,
			text=True,
		)

		log_path.write_text(result.stdout + "\n" + result.stderr)

		if result.returncode != 0:
			any_failure = True
			print(
				f"[ERROR] Packager failed for {spec_path.name}. See {log_path.name} for details."
			)
		else:
			print(f"[OK] Created {output_zip.name}")

	if any_failure:
		print("[WARN] Some files failed. Review the logs above.")
		return 1

	print("[DONE] All DropZone files processed successfully.")
	return 0


if __name__ == "__main__":
	sys.exit(main())
