"""Run alembic upgrade head to apply all migrations."""
import subprocess
import sys
from pathlib import Path


def main() -> None:
    backend_dir = Path(__file__).parent.parent
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"Migration failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print("Database migrations applied successfully.")


if __name__ == "__main__":
    main()