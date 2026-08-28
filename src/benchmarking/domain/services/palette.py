"""Thesis Visualization Palette & Semantic Dynamic Styling Engine.

Provides a fully dynamic, rule-based visualization system that decomposes any present
or future solver into its orthogonal semantic components (Classical baseline vs.
LLM backbone, parameter scale, and prompt engineering strategy).

Zero manual model hardcoding required: Any new model added to configs/llms.toml or benchmarked
in the future is automatically assigned calibrated, publication-grade colors, stroke widths,
and dash patterns based on semantic rules.
"""

from collections.abc import Sequence
import colorsys
import re
from typing import Final

FONT_FAMILY: Final[str] = "Inter, -apple-system, BlinkMacSystemFont, Arial, sans-serif"

# ─── 1. Semantic Strategy Archetype Tones (Calibrated for Thesis Theme) ──────
# Maps prompt engineering strategies to scale-differentiated color pairs (Large vs. Small model scale)
STRATEGY_COLOR_ARCHETYPES: Final[dict[str, dict[str, str]]] = {
    # Blue Spectrum: Royal Blue (Flagship/Large) vs. Sky Blue (Small)
    "guided": {
        "large": "#1D4ED8",
        "small": "#38BDF8",
        "base": "#2563EB",
    },
    # Green Spectrum: Deep Emerald (Flagship/Large) vs. Mint Spring (Small)
    "thinking": {
        "large": "#047857",
        "small": "#34D399",
        "base": "#059669",
    },
    # Red Spectrum: Deep Crimson (Flagship/Large) vs. Coral Salmon (Small)
    "vectorization": {
        "large": "#B91C1C",
        "small": "#F87171",
        "base": "#DC2626",
    },
    # Amber/Gold Spectrum: Deep Ochre (Flagship/Large) vs. Sun Gold (Small)
    "baseline": {
        "large": "#B45309",
        "small": "#FBBF24",
        "base": "#D97706",
    },
}

STRATEGY_PALETTE: Final[dict[str, str]] = {
    k: v["base"] for k, v in STRATEGY_COLOR_ARCHETYPES.items()
}

# ─── 2. Classical Baseline Archetypes ───────────────────────────────────────
CLASSICAL_SOLVERS_STYLE: Final[dict[str, dict]] = {
    "cma-es": {"color": "#0F172A", "dash": "dash", "width": 2.2, "name": "CMA-ES"},
    "pso":    {"color": "#0D9488", "dash": "dashdot", "width": 2.2, "name": "PSO"},
    "de":     {"color": "#7C3AED", "dash": "dot", "width": 2.2, "name": "DE"},
}

# ─── 3. Environmental Duality (Clean vs. Noisy) ─────────────────────────────
REGIME_PALETTE: Final[dict[str, dict]] = {
    "clean": {
        "color": "#1D4ED8",
        "border": "#0F172A",
        "name": "Clean (σ=0.0)",
        "pattern": None,
    },
    "noisy": {
        "color": "#EA580C",
        "border": "#7C2D12",
        "name": "Noisy (σ=0.05)",
        "pattern": {"shape": "/", "fillmode": "replace", "fgcolor": "#FFFFFF", "fgopacity": 0.35, "size": 6},
    },
}

# ─── 4. Problem Dimension Gradient (2D, 3D, 5D) ─────────────────────────────
DIMENSION_PALETTE_CLEAN: Final[dict[int, str]] = {
    2: "#93C5FD",  # Light Blue
    3: "#3B82F6",  # Medium Blue
    5: "#1D4ED8",  # Deep Blue
}

DIMENSION_PALETTE_NOISY: Final[dict[int, str]] = {
    2: "#FDBA74",  # Light Orange
    3: "#FB923C",  # Medium Orange
    5: "#EA580C",  # Dark Terracotta
}

# ─── 5. Model Scale Ablation Palette (Figure 9E) ────────────────────────────
MODEL_SCALE_PALETTE: Final[dict[str, str]] = {
    "Qwen2.5-Coder-7B": "#38BDF8",
    "Qwen2.5-Coder-14B": "#0284C7",
}


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL color coordinates (0..1) to 6-character hex string."""
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(
        int(round(max(0.0, min(1.0, r)) * 255)),
        int(round(max(0.0, min(1.0, g)) * 255)),
        int(round(max(0.0, min(1.0, b)) * 255)),
    )


# In-memory cache for resolved solver styles
_DYNAMIC_STYLE_CACHE: dict[str, dict] = {}


def get_solver_line_style(solver_name: str) -> dict:
    """Dynamically resolve color, dash pattern, and stroke width for any solver.

    Deconstructs solver name into:
    1. Classical baseline check (CMA-ES, PSO, DE).
    2. LLM solver structure (`<ModelTag> / <Strategy>`).
       - Strategy maps to semantic color family.
       - Model scale (B parameter size) determines large (>=14B, deep bold 2.5px) vs small (<14B, tinted 1.8px).
       - Novel/unknown strategies dynamically generate golden-ratio distinct hues.
    3. Unstructured fallback (deterministic golden-ratio color stepping).
    """
    if not solver_name:
        return {"color": "#64748B", "dash": "solid", "width": 2.0}

    s = str(solver_name).strip()
    s_lower = s.lower()

    if s in _DYNAMIC_STYLE_CACHE:
        return _DYNAMIC_STYLE_CACHE[s]

    # 1. Classical Baselines (Exact match)
    if s_lower in CLASSICAL_SOLVERS_STYLE:
        res = CLASSICAL_SOLVERS_STYLE[s_lower].copy()
        _DYNAMIC_STYLE_CACHE[s] = res
        return res

    # 2. LLM Synthesized Solvers (<ModelTag> / <Strategy>)
    if " / " in s:
        model_part, strat_part = s.split(" / ", 1)
        strat_key = strat_part.strip().lower()

        # Extract Model Scale (B size)
        size_match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]", model_part)
        if size_match:
            size_b = float(size_match.group(1))
            is_large = size_b >= 14.0
        else:
            is_large = True

        scale_key = "large" if is_large else "small"
        line_width = 2.5 if is_large else 1.8

        if strat_key in STRATEGY_COLOR_ARCHETYPES:
            hex_color = STRATEGY_COLOR_ARCHETYPES[strat_key][scale_key]
        else:
            # Deterministic golden-ratio distributed hue for any unseen strategy
            base_hue = (abs(hash(strat_key)) * 0.618033988749895) % 1.0
            hex_color = hsl_to_hex(base_hue, s=0.85, l=0.45 if is_large else 0.62)

        res = {"color": hex_color, "dash": "solid", "width": line_width}
        _DYNAMIC_STYLE_CACHE[s] = res
        return res

    # 3. Dynamic Unstructured Fallback
    hue = (abs(hash(s_lower)) * 0.618033988749895) % 1.0
    hex_color = hsl_to_hex(hue, s=0.75, l=0.50)
    res = {"color": hex_color, "dash": "dash", "width": 2.0}
    _DYNAMIC_STYLE_CACHE[s] = res
    return res


def get_solver_color(solver_name: str) -> str:
    """Retrieve canonical high-contrast color for any solver dynamically."""
    return get_solver_line_style(solver_name)["color"]


def get_rgba_fill(hex_color: str, opacity: float = 0.12) -> str:
    """Convert hex color string to rgba string with specified opacity for shaded error bands."""
    if hex_color.startswith("#") and len(hex_color) == 7:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"
    return f"rgba(100, 116, 139, {opacity})"


def get_dimension_color(dim: int, is_noisy: bool = False) -> str:
    """Get calibrated color for problem dimensionality in clean vs. noisy regimes."""
    if is_noisy:
        return DIMENSION_PALETTE_NOISY.get(dim, "#FB923C")
    return DIMENSION_PALETTE_CLEAN.get(dim, "#3B82F6")


def build_dynamic_solver_palette(solvers: Sequence[str]) -> dict[str, str]:
    """Populate and return complete color map for an iterable of solver names dynamically."""
    return {s: get_solver_color(s) for s in solvers}


class DynamicSolverPalette(dict):
    """Dynamic dict that resolves any solver on the fly without hardcoded key restrictions."""
    def __getitem__(self, key: str) -> str:
        return get_solver_color(key)

    def get(self, key: str, default: str = None) -> str:
        if not key:
            return default or "#64748B"
        return get_solver_color(key)


SOLVER_PALETTE: Final[DynamicSolverPalette] = DynamicSolverPalette()
SOLVER_LINE_STYLES: Final[dict[str, dict]] = {}
