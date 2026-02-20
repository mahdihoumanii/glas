"""
Model configuration utilities for GLAS.

Models define both the QGRAF model file and the FORM Feynman rules procedure.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from glaslib.core.paths import resources_dir


@dataclass
class ModelInfo:
    """Information about a physics model."""
    id: str
    name: str
    description: str
    qgraf_model: str
    feynman_rules_prc: str


def _models_json_path() -> Path:
    """Return path to models.json configuration file."""
    return resources_dir() / "formlib" / "models.json"


def load_models_config() -> Dict:
    """Load the models.json configuration file."""
    path = _models_json_path()
    if not path.exists():
        raise FileNotFoundError(f"models.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_available_models() -> List[ModelInfo]:
    """Return list of all available models."""
    config = load_models_config()
    models = []
    for m in config.get("models", []):
        models.append(ModelInfo(
            id=m["id"],
            name=m["name"],
            description=m["description"],
            qgraf_model=m.get("qgraf_model", "qcd"),
            feynman_rules_prc=m["feynman_rules_prc"],
        ))
    return models


def get_default_model_id() -> str:
    """Return the default model ID from configuration."""
    config = load_models_config()
    return config.get("default", "qcd_massive")


def get_model_by_id(model_id: str) -> Optional[ModelInfo]:
    """Get model info by ID. Returns None if not found."""
    for model in get_available_models():
        if model.id == model_id:
            return model
    return None


def get_feynman_rules_prc(model_id: str) -> str:
    """
    Get the Feynman rules procedure filename for a given model ID.
    
    Falls back to default FeynmanRules.prc if model not found (backward compatibility).
    """
    model = get_model_by_id(model_id)
    if model:
        return model.feynman_rules_prc
    # Backward compatibility: unknown model_id uses default
    return "FeynmanRules.prc"


def get_qgraf_model(model_id: str) -> str:
    """
    Get the QGRAF model file name for a given model ID.
    
    Falls back to "qcd" if model not found (backward compatibility).
    """
    model = get_model_by_id(model_id)
    if model:
        return model.qgraf_model
    # Backward compatibility: unknown model_id uses qcd
    return "qcd"


def resolve_model_id(run_model_id: Optional[str], global_model_id: str) -> str:
    """
    Resolve which model_id to use.
    
    Priority:
    1. Run-specific model_id (from meta.json) if present
    2. Global active model (from AppState)
    """
    if run_model_id:
        return run_model_id
    return global_model_id


def get_mass_for_particle(token: str, model_id: str) -> str:
    """
    Get the mass symbol for a particle token based on model_id.
    
    For qcd_massless: all masses are 0
    For other models: t/t~ -> mt, h -> mH, others -> 0
    """
    # Massless model: all masses are 0
    if model_id == "qcd_massless":
        return "0"
    
    # Standard mass assignment
    tok = token.lower()
    if tok in ("t", "t~", "tbar"):
        return "mt"
    if tok in ("h", "higgs"):
        return "mH"
    return "0"


def print_available_models(header: bool = True) -> None:
    """Print available models to stdout."""
    models = get_available_models()
    default_id = get_default_model_id()
    
    if header:
        print("Available models:")
    
    for i, m in enumerate(models, 1):
        default_marker = " (default)" if m.id == default_id else ""
        print(f"  {i}) {m.name}{default_marker}")
        print(f"     {m.description}")
