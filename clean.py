import logging
import shutil
import subprocess
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("clean")

BASE_DIR = Path(__file__).resolve().parent
OS_BUILDER_DIR = BASE_DIR / "os_builder"


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return

    logger.info("Removing %s...", path.relative_to(BASE_DIR))
    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
    except PermissionError:
        subprocess.run(["sudo", "rm", "-rf", str(path)], check=True)


def remove_pkg_cross_archives(pkg_cross_dir: Path) -> None:
    if not pkg_cross_dir.exists():
        return

    for archive in pkg_cross_dir.rglob("*.tar"):
        remove_path(archive)


def main() -> int:
    logger.info("Cleaning...")

    for path in (
        BASE_DIR / "releases",
        BASE_DIR / "build",
        BASE_DIR / "pkg_built",
        OS_BUILDER_DIR / "releases",
        OS_BUILDER_DIR / "build",
        OS_BUILDER_DIR / "pkg_built",
    ):
        remove_path(path)

    remove_pkg_cross_archives(BASE_DIR / "pkg_cross")
    remove_pkg_cross_archives(OS_BUILDER_DIR / "pkg_cross")

    logger.info("Clean finished.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Clean command failed with exit code %s: %s",
            exc.returncode,
            exc.cmd,
        )
        raise SystemExit(exc.returncode)
    except OSError as exc:
        logger.error("Clean failed: %s", exc)
        raise SystemExit(1)
