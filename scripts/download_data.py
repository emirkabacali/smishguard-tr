"""Download the TurkishSMS dataset (Uysal et al., 2013) into data/raw/.

The dataset license allows academic use only, so the files are never committed; this script
fetches them reproducibly instead. Sources are tried in order:

1. The first author's Hugging Face mirror, pinned to an exact revision (checksums verified).
2. The same mirror at the latest revision (checksums logged, mismatch only warned).

If both fail, the script exits with instructions for a manual download.

Usage:
    python scripts/download_data.py [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
import urllib.error
import urllib.request
from pathlib import Path

from smishguard import config

logger = logging.getLogger("download_data")

HF_URL_TEMPLATE = "https://huggingface.co/datasets/{repo}/resolve/{revision}/{path}"


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, target: Path) -> None:
    """Download ``url`` to ``target`` atomically (write to a temp file, then rename)."""
    tmp = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "smishguard-tr-downloader"})
    with urllib.request.urlopen(request, timeout=config.DOWNLOAD_TIMEOUT_SECONDS) as response:
        tmp.write_bytes(response.read())
    tmp.replace(target)


def try_revision(revision: str, raw_dir: Path, strict: bool) -> bool:
    """Download all TurkishSMS files from one Hugging Face revision.

    Args:
        revision: Git revision (commit SHA or branch) of the HF dataset repo.
        raw_dir: Destination directory.
        strict: If True, a checksum mismatch counts as a failure.

    Returns:
        True if every file was downloaded (and verified when ``strict``).
    """
    for filename, (remote_path, expected_sha) in config.TURKISHSMS_FILES.items():
        url = HF_URL_TEMPLATE.format(
            repo=config.TURKISHSMS_HF_REPO, revision=revision, path=remote_path
        )
        target = raw_dir / filename
        try:
            fetch(url, target)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            logger.warning("Download failed (%s): %s", url, exc)
            return False

        actual_sha = sha256_of(target)
        logger.info("%s sha256=%s", filename, actual_sha)
        if actual_sha != expected_sha:
            if strict:
                logger.warning("Checksum mismatch for %s (expected %s)", filename, expected_sha)
                target.unlink()
                return False
            logger.warning("Checksum differs from the pinned revision for %s", filename)
    return True


def files_present(raw_dir: Path) -> bool:
    """Return True if all expected files exist and match the pinned checksums."""
    for filename, (_, expected_sha) in config.TURKISHSMS_FILES.items():
        path = raw_dir / filename
        if not path.exists() or sha256_of(path) != expected_sha:
            return False
    return True


def main() -> int:
    """Entry point. Returns a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="re-download existing files")
    args = parser.parse_args()

    raw_dir = config.RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    if not args.force and files_present(raw_dir):
        logger.info("TurkishSMS already present and verified in %s", raw_dir)
        return 0

    attempts = ((config.TURKISHSMS_HF_REVISION, True), ("main", False))
    for revision, strict in attempts:
        logger.info("Trying %s @ %s", config.TURKISHSMS_HF_REPO, revision)
        if try_revision(revision, raw_dir, strict=strict):
            logger.info("TurkishSMS downloaded to %s", raw_dir)
            return 0

    expected = ", ".join(config.TURKISHSMS_FILES)
    manual = "\n  ".join(config.TURKISHSMS_MANUAL_SOURCES)
    logger.error(
        "Could not download TurkishSMS automatically.\n"
        "Download it manually from one of:\n  %s\n"
        "or https://huggingface.co/datasets/%s and place these files in %s: %s",
        manual,
        config.TURKISHSMS_HF_REPO,
        raw_dir,
        expected,
    )
    return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(main())
