""" v0.002 """
from pathlib import Path
import shutil
import sys
from typing import Generator
import re

SCRIPT_DIR = Path(__file__).parent.resolve()
ADDON_NAME = SCRIPT_DIR.stem
RELEASES_DIR = SCRIPT_DIR / "releases"
WHITELIST_SRC = SCRIPT_DIR / "release_whitelist.txt"
INIT_FILE = SCRIPT_DIR / "__init__.py"


def package_release():
    script_version = get_version()
    RELEASES_DIR.mkdir(exist_ok=True)
    output_dir = RELEASES_DIR / ADDON_NAME
    if output_dir.exists():
        handle_existing_output_dir(output_dir)
    print(f"Creating output directory {output_dir}")
    output_dir.mkdir()

    whitelist = list(load_whitelist())

    for item in whitelist:
        for result in SCRIPT_DIR.glob(item):
            if result.is_file():
                shutil.copy(str(result), str(output_dir))
            if result.is_dir():
                dst = output_dir / result.name
                shutil.copytree(str(result), str(dst), symlinks=False)

    archive_path = RELEASES_DIR / f"{SCRIPT_DIR.name}_{script_version}"
    if archive_path.with_suffix(".zip").exists():
        print(f"Removing existing archive {archive_path}")
        archive_path.with_suffix(".zip").unlink()

    print(f"Packaging {ADDON_NAME} to {archive_path}")
    print(RELEASES_DIR)
    print(output_dir)
    shutil.make_archive(
        str(archive_path), "zip",
        root_dir=str(RELEASES_DIR),
        base_dir=ADDON_NAME
    )

    shutil.rmtree(str(output_dir))


def load_whitelist() -> Generator[str, None, None]:
    with open(WHITELIST_SRC, "r") as whitelist_file:
        for line in whitelist_file:
            yield line.strip("\n")


def handle_existing_output_dir(output_dir: Path):
    print(f"Output dir {output_dir} already exists")
    user_confirm = input("Remove existing?: ")
    if user_confirm.lower() == "y":
        print("Removing Existing Directory")
        shutil.rmtree(str(output_dir))
    else:
        print("Cancelling")
        sys.exit()


def get_version() -> str:
    def _is_version_line(line) -> bool:
        return '"version":' in line

    def _parse_version_line(line) -> str:
        # eg. "version": (0, 2, 0),
        pattern = r"(\d+)"
        results = re.findall(pattern, line)
        as_string = results[0]
        for number in results[1:]:
            as_string += f"_{number}"
        return as_string

    with open(INIT_FILE, "r") as init_file:
        version_line = next(filter(_is_version_line, init_file))
        return _parse_version_line(version_line)


if __name__ == "__main__":
    package_release()