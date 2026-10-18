"""Assemble with the unchanged course tools and record their diagnostics."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def build():
    for tool, log in (("as21.py", "assemble.log"), ("lister.py", "listing.log")):
        proc = subprocess.run(
            [sys.executable, str(HERE.parent / "tools" / tool)],
            input="stopwatch.txt\n", text=True, capture_output=True, cwd=HERE,
        )
        output = proc.stdout + proc.stderr
        (HERE / log).write_text(output, encoding="utf-8")
        if proc.returncode or "error" in output.lower():
            raise RuntimeError(f"{tool} failed; see {log}\n{output}")
    print("Built stopwatch.obj and stopwatch.lis using the copied course tools.")


if __name__ == "__main__":
    build()
