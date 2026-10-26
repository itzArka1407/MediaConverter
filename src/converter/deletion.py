"""Used to delete file(s) from a directory or the file path itself"""

from pathlib import Path

def delete_file(src: Path, dry_run: bool):
    """Delete a file from the specified path -- dry run is performed for dev"""
    if src.is_file():
        if dry_run:
            print(f"[DRY RUN]: Would delete: {src}")
        else:
            print(f"DELETING: {src}")
            src.unlink(missing_ok=True)
