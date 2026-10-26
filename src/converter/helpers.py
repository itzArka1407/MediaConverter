"""Helper functions to be used across the project """

from pathlib import Path

def is_dev_install() -> bool:
    """Checks the presence of pyproject.toml file(only present in the dev mode as per the constraints)"""
    return (Path(__file__).resolve().parents[2] / "pyproject.toml").exists()

DEV_MODE = is_dev_install()
