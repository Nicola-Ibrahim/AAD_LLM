"""Shared typography and deterministic Plotly solver styles."""

import colorsys
import hashlib
import re

CLASSICAL_BASELINES = ["CMA-ES", "PSO", "DE"]

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, Arial, sans-serif"

STRATEGY_COLOR_ARCHETYPES = {
    "guided": {"large": "#38BDF8", "small": "#38BDF8", "base": "#38BDF8"},
    "thinking": {"large": "#34D399", "small": "#34D399", "base": "#34D399"},
    "vectorization": {"large": "#F87171", "small": "#F87171", "base": "#F87171"},
    "baseline": {"large": "#FBBF24", "small": "#FBBF24", "base": "#FBBF24"},
}
CLASSICAL_SOLVERS_STYLE = {
    "cma-es": {"color": "#334155", "dash": "solid", "width": 2.2},
    "pso": {"color": "#0D9488", "dash": "solid", "width": 2.2},
    "de": {"color": "#7C3AED", "dash": "solid", "width": 2.2},
}
MODEL_SCALE_PALETTE = {
    "Qwen2.5-Coder-14B-Instruct": "#0284C7",
    "Qwen2.5-Coder-32B-Instruct": "#0369A1",
}


def get_model_scale_color(model_name: str, models: list[str] | dict[str, list[str]]) -> str:
    m_clean = model_name.strip().lower()
    for model_tag, color in MODEL_SCALE_PALETTE.items():
        if model_tag.lower() == m_clean:
            return color
    fallback_colors = ["#7C3AED", "#0F766E", "#D97706", "#DB2777", "#475569"]
    dynamic_models = sorted(models)
    model_index = dynamic_models.index(model_name)
    return fallback_colors[model_index % len(fallback_colors)]


def stable_hue(label: str) -> float:
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], byteorder="big") / 0xFFFFFFFF


def clean_solver_name(solver_name: str) -> str:
    return solver_name.replace(" (noise-adapted)", "").replace(" (noise-implicit)", "").strip()


def hsl_to_hex(h: float, s: float, lightness: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h, lightness, s)
    return "#{:02X}{:02X}{:02X}".format(
        int(round(max(0.0, min(1.0, r)) * 255)),
        int(round(max(0.0, min(1.0, g)) * 255)),
        int(round(max(0.0, min(1.0, b)) * 255)),
    )


_DYNAMIC_STYLE_CACHE: dict[str, dict[str, str | float]] = {}


def get_solver_line_style(solver_name: str) -> dict[str, str | float]:
    if not solver_name:
        return {"color": "#64748B", "dash": "solid", "width": 2.0}
    s = solver_name.strip()
    s_lower = s.lower()
    if s in _DYNAMIC_STYLE_CACHE:
        return _DYNAMIC_STYLE_CACHE[s]
    if s_lower in CLASSICAL_SOLVERS_STYLE:
        res = CLASSICAL_SOLVERS_STYLE[s_lower].copy()
        _DYNAMIC_STYLE_CACHE[s] = res
        return res
    if " / " in s:
        model_part, strat_part = s.split(" / ", 1)
        strat_key = strat_part.strip().lower()
        size_match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]", model_part)
        is_large = float(size_match.group(1)) >= 14.0 if size_match else True
        scale_key = "large" if is_large else "small"
        line_width = 2.5 if is_large else 1.8
        if strat_key in STRATEGY_COLOR_ARCHETYPES:
            hex_color = STRATEGY_COLOR_ARCHETYPES[strat_key][scale_key]
        else:
            base_hue = stable_hue(strat_key)
            hex_color = hsl_to_hex(base_hue, s=0.85, lightness=0.45 if is_large else 0.62)
        res = {"color": hex_color, "dash": "dash", "width": line_width}
        _DYNAMIC_STYLE_CACHE[s] = res
        return res
    hue = stable_hue(s_lower)
    hex_color = hsl_to_hex(hue, s=0.75, lightness=0.50)
    res = {"color": hex_color, "dash": "dash", "width": 2.0}
    _DYNAMIC_STYLE_CACHE[s] = res
    return res


def get_solver_color(solver_name: str) -> str:
    return str(get_solver_line_style(solver_name)["color"])


def get_rgba_fill(hex_color: str, opacity: float = 0.12) -> str:
    if hex_color.startswith("#") and len(hex_color) == 7:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"
    return f"rgba(100, 116, 139, {opacity})"
