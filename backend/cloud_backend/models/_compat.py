from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_LEGACY_MODELS_DIR = Path(__file__).resolve().parents[2] / "models" / "models"


@lru_cache(maxsize=None)
def load_symbol(module_name: str, symbol_name: str):
    module_path = _LEGACY_MODELS_DIR / f"{module_name}.py"
    spec = spec_from_file_location(f"cloud_backend_legacy_models_{module_name}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load legacy model module: {module_path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, symbol_name)