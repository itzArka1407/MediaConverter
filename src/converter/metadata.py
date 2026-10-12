from importlib.metadata import version, PackageNotFoundError 

def get_version() -> str:
    """From the package toml file, get the version of the product"""
    try:
        return version("media-converter")
    except PackageNotFoundError:
        return "0.0.0+unknown"
