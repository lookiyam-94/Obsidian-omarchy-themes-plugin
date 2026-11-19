#!/usr/bin/env python3
"""Build the Obsidian theme bundle from Omarchy colors.toml files.

The four roles match omarchy-vivaldi-themes ``build.py``:

    background        main surfaces            Vivaldi colorBg
    dark_background   tab bar and side chrome  Vivaldi colorAccentBg and colorWindowBg
    foreground        text                     Vivaldi colorFg
    accent            focus and selection      Vivaldi colorHighlightBg

Other Obsidian slots (headings, links, code, borders) use further keys from
the same colors.toml. No new hex values are mixed.

    python3 scripts/generate.py
    python3 scripts/generate.py --check
    python3 scripts/generate.py --themes /usr/share/omarchy/themes
    python3 scripts/generate.py --only nord tokyo-night
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_THEMES = os.path.join(ROOT, "palettes")
DEFAULT_OUT = os.path.join(ROOT, "src", "themes.generated.json")
DEFAULT_CSS = os.path.join(ROOT, "styles.css")

STATIC_CSS = """\
.omarchy-swatches {
	display: flex;
	gap: 8px;
	margin: 4px 0 12px;
}

.omarchy-swatch {
	width: 28px;
	height: 28px;
	border-radius: 6px;
	border: 1px solid var(--background-modifier-border);
}
"""

# Names that do not survive a plain title-case of the directory name.
# Kept in step with omarchy-vivaldi-themes build.py.
TITLES = {
    "catppuccin-latte": "Catppuccin Latte",
    "osaka-jade": "Osaka Jade",
    "retro-82": "Retro-82",
}

SOURCES = {
    "jade-horse": "omacom/omarchy tag v4.5.0 themes/jade-horse/colors.toml",
    "starship": "omacom/omarchy branch quattro themes/starship/colors.toml",
    "dracula": "catlee/omarchy-dracula-theme via omarchy-vivaldi-themes sources/dracula",
    "rose-pine-dark": "guilhermetk/omarchy-rose-pine-dark via omarchy-vivaldi-themes sources/rose-pine-dark",
}
DEFAULT_SOURCE = "omacom/omarchy tag v4.0.4 themes/<id>/colors.toml"

REQUIRED = (
    "mode",
    "accent",
    "selection",
    "muted",
    "background",
    "dark_background",
    "darker_background",
    "lighter_background",
    "foreground",
    "dark_foreground",
    "light_foreground",
    "bright_foreground",
    "red",
    "yellow",
    "green",
    "cyan",
    "blue",
    "magenta",
    "bright_red",
    "bright_yellow",
    "bright_green",
    "bright_cyan",
    "bright_blue",
    "bright_magenta",
)

BASE_STEPS = ("00", "05", "10", "20", "25", "30", "35", "40", "50", "60", "70", "100")
RAMP_KEYS = (
    "darker_background",
    "dark_background",
    "background",
    "lighter_background",
    "selection",
    "muted",
    "dark_foreground",
    "light_foreground",
    "foreground",
    "bright_foreground",
)


def title_of(slug: str) -> str:
    return TITLES.get(slug, slug.replace("-", " ").title())


def channel(value: float) -> float:
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    raw = hex_color[1:]
    red = channel(int(raw[0:2], 16) / 255)
    green = channel(int(raw[2:4], 16) / 255)
    blue = channel(int(raw[4:6], 16) / 255)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(left: str, right: str) -> float:
    lighter = max(luminance(left), luminance(right))
    darker = min(luminance(left), luminance(right))
    return (lighter + 0.05) / (darker + 0.05)


def rgb_triplet(hex_color: str) -> str:
    raw = hex_color[1:]
    return f"{int(raw[0:2], 16)}, {int(raw[2:4], 16)}, {int(raw[4:6], 16)}"


def accent_hsl(hex_color: str) -> dict[str, str]:
    raw = hex_color[1:]
    red = int(raw[0:2], 16) / 255
    green = int(raw[2:4], 16) / 255
    blue = int(raw[4:6], 16) / 255
    high = max(red, green, blue)
    low = min(red, green, blue)
    light = (high + low) / 2
    if high == low:
        hue = 0.0
        saturation = 0.0
    else:
        delta = high - low
        saturation = delta / (2 - high - low) if light > 0.5 else delta / (high + low)
        if high == red:
            hue = ((green - blue) / delta) % 6
        elif high == green:
            hue = (blue - red) / delta + 2
        else:
            hue = (red - green) / delta + 4
        hue /= 6
    return {
        "h": str(round(hue * 360) % 360),
        "s": f"{round(saturation * 100)}%",
        "l": f"{round(light * 100)}%",
    }


def rank_contrast(first: str, second: str, against: str) -> tuple[str, str]:
    """Return (more readable, fainter) of two palette colours on ``against``."""
    if contrast(first, against) >= contrast(second, against):
        return first, second
    return second, first


def best_on_accent(palette: dict[str, str]) -> tuple[str, str]:
    options = [
        palette["background"],
        palette["dark_background"],
        palette["darker_background"],
        palette["foreground"],
        palette["bright_foreground"],
    ]
    unique: list[str] = []
    seen: set[str] = set()
    for color in options:
        if color not in seen:
            seen.add(color)
            unique.append(color)
    ranked = sorted(unique, key=lambda color: contrast(color, palette["accent"]), reverse=True)
    return ranked[0], ranked[-1]


def load_palette(path: str) -> dict[str, str]:
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)
    missing = [key for key in REQUIRED if key not in raw]
    if missing:
        raise SystemExit(f"{path} is missing {', '.join(missing)}")
    mode = raw["mode"]
    if mode not in ("light", "dark"):
        raise SystemExit(f"{path} has mode {mode!r}; expected light or dark")
    palette: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(value, str) or not value.startswith("#"):
            continue
        if len(value) != 7:
            raise SystemExit(f"{path} key {key} is {value!r}; expected #rrggbb")
        palette[key] = value
    for key in REQUIRED:
        if key == "mode":
            continue
        if key not in palette:
            raise SystemExit(f"{path} key {key} is not a #rrggbb colour")
    return palette


def color_or(palette: dict[str, str], key: str, fallback: str) -> tuple[str, str | None]:
    if key in palette:
        return palette[key], None
    return palette[fallback], f"{key} -> {fallback}"


def base_ramp(palette: dict[str, str], mode: str) -> dict[str, str]:
    colors: list[str] = []
    seen: set[str] = set()
    for key in RAMP_KEYS:
        value = palette[key]
        if value.lower() in seen:
            continue
        seen.add(value.lower())
        colors.append(value)
    colors.sort(key=luminance, reverse=(mode == "light"))
    last = len(colors) - 1
    ramp: dict[str, str] = {}
    for index, step in enumerate(BASE_STEPS):
        pick = round(index * last / (len(BASE_STEPS) - 1)) if last else 0
        ramp[f"--color-base-{step}"] = colors[pick]
    return ramp


def css_variables(palette: dict[str, str], mode: str) -> tuple[dict[str, str], list[str]]:
    muted_text, faint_text = rank_contrast(
        palette["dark_foreground"], palette["muted"], palette["background"]
    )
    on_accent, on_accent_inverted = best_on_accent(palette)
    orange, orange_note = color_or(palette, "orange", "yellow")
    fallbacks = [orange_note] if orange_note else []
    hsl = accent_hsl(palette["accent"])

    css: dict[str, str] = {}
    css.update(base_ramp(palette, mode))
    css.update(
        {
            "--background-primary": palette["background"],
            "--background-primary-alt": palette["lighter_background"],
            "--background-secondary": palette["dark_background"],
            "--background-secondary-alt": palette["darker_background"],
            "--background-modifier-hover": palette["selection"],
            "--background-modifier-active-hover": palette["selection"],
            "--background-modifier-border": palette["selection"],
            "--background-modifier-border-hover": palette["muted"],
            "--background-modifier-border-focus": palette["accent"],
            "--background-modifier-form-field": palette["darker_background"],
            "--divider-color": palette["selection"],
            "--interactive-normal": palette["lighter_background"],
            "--interactive-hover": palette["selection"],
            "--interactive-accent": palette["accent"],
            "--interactive-accent-hover": palette["accent"],
            "--interactive-accent-hsl": f"{hsl['h']}, {hsl['s']}, {hsl['l']}",
            "--color-accent": palette["accent"],
            "--color-accent-1": palette["accent"],
            "--color-accent-2": palette["accent"],
            "--text-normal": palette["foreground"],
            "--text-muted": muted_text,
            "--text-faint": faint_text,
            "--text-accent": palette["accent"],
            "--text-accent-hover": palette["accent"],
            "--text-on-accent": on_accent,
            "--text-on-accent-inverted": on_accent_inverted,
            "--text-selection": palette["accent"],
            "--text-highlight-bg": palette["accent"],
            "--text-error": palette["red"],
            "--text-success": palette["green"],
            "--text-warning": palette["yellow"],
            "--caret-color": palette["accent"],
            "--h1-color": palette["bright_foreground"],
            "--h2-color": palette["foreground"],
            "--h3-color": palette["foreground"],
            "--h4-color": palette["foreground"],
            "--h5-color": palette["foreground"],
            "--h6-color": palette["foreground"],
            "--heading-formatting": palette["accent"],
            "--inline-title-color": palette["bright_foreground"],
            "--bold-color": palette["bright_foreground"],
            "--italic-color": palette["foreground"],
            "--link-color": palette["accent"],
            "--link-color-hover": palette["accent"],
            "--link-external-color": palette["blue"],
            "--link-external-color-hover": palette["bright_blue"],
            "--link-unresolved-color": palette["muted"],
            "--code-background": palette["darker_background"],
            "--code-normal": palette["foreground"],
            "--code-comment": faint_text,
            "--code-keyword": palette["magenta"],
            "--code-string": palette["green"],
            "--code-function": palette["blue"],
            "--code-value": palette["yellow"],
            "--code-operator": palette["cyan"],
            "--code-property": palette["cyan"],
            "--code-punctuation": faint_text,
            "--code-tag": orange,
            "--code-important": palette["red"],
            "--titlebar-background": palette["dark_background"],
            "--titlebar-background-focused": palette["dark_background"],
            "--tab-container-background": palette["dark_background"],
            "--tab-background-active": palette["background"],
            "--tab-text-color": faint_text,
            "--tab-text-color-active": palette["foreground"],
            "--tab-text-color-focused": palette["foreground"],
            "--tab-text-color-focused-active": palette["foreground"],
            "--tab-outline-color": palette["accent"],
            "--ribbon-background": palette["dark_background"],
            "--status-bar-background": palette["dark_background"],
            "--nav-item-color": palette["foreground"],
            "--nav-item-color-hover": palette["foreground"],
            "--nav-item-color-active": palette["accent"],
            "--nav-item-background-hover": palette["selection"],
            "--nav-item-background-active": palette["selection"],
            "--scrollbar-bg": palette["dark_background"],
            "--scrollbar-thumb-bg": palette["muted"],
            "--scrollbar-active-thumb-bg": palette["dark_foreground"],
            "--tag-color": palette["accent"],
            "--tag-background": palette["selection"],
            "--blockquote-border-color": palette["accent"],
            "--list-marker-color": palette["accent"],
            "--color-red": palette["red"],
            "--color-orange": orange,
            "--color-yellow": palette["yellow"],
            "--color-green": palette["green"],
            "--color-cyan": palette["cyan"],
            "--color-blue": palette["blue"],
            "--color-purple": palette["magenta"],
            "--color-pink": palette["bright_magenta"],
            "--color-red-rgb": rgb_triplet(palette["red"]),
            "--color-orange-rgb": rgb_triplet(orange),
            "--color-yellow-rgb": rgb_triplet(palette["yellow"]),
            "--color-green-rgb": rgb_triplet(palette["green"]),
            "--color-cyan-rgb": rgb_triplet(palette["cyan"]),
            "--color-blue-rgb": rgb_triplet(palette["blue"]),
            "--color-purple-rgb": rgb_triplet(palette["magenta"]),
            "--color-pink-rgb": rgb_triplet(palette["bright_magenta"]),
            "--interactive-accent-rgb": rgb_triplet(palette["accent"]),
        }
    )
    return css, fallbacks


def build_theme(slug: str, path: str) -> dict[str, object]:
    with open(path, "rb") as handle:
        mode = tomllib.load(handle)["mode"]
    palette = load_palette(path)
    css, fallbacks = css_variables(palette, mode)
    return {
        "id": slug,
        "name": title_of(slug),
        "mode": mode,
        "source": SOURCES.get(slug, DEFAULT_SOURCE),
        "palette": dict(sorted(palette.items())),
        "vivaldi": {
            "colorBg": palette["background"],
            "colorAccentBg": palette["dark_background"],
            "colorWindowBg": palette["dark_background"],
            "colorFg": palette["foreground"],
            "colorHighlightBg": palette["accent"],
        },
        "accentHsl": accent_hsl(palette["accent"]),
        "fallbacks": fallbacks,
        "cssVariables": css,
    }


def collect(theme_dirs: list[str], only: list[str] | None) -> list[tuple[str, str]]:
    found: dict[str, str] = {}
    for directory in theme_dirs:
        if not os.path.isdir(directory):
            raise SystemExit(f"themes directory not found: {directory}")
        for slug in sorted(os.listdir(directory)):
            path = os.path.join(directory, slug, "colors.toml")
            if not os.path.isfile(path):
                continue
            if only and slug not in only:
                continue
            if slug in found:
                raise SystemExit(f"{slug} appears in both {found[slug]} and {path}")
            found[slug] = path
    if not found:
        raise SystemExit("no colors.toml files found")
    return sorted(found.items())


def bundle_text(themes: list[dict[str, object]]) -> str:
    payload = {
        "themes": themes,
    }
    return json.dumps(payload, indent=2) + "\n"


def stylesheet(themes: list[dict[str, object]]) -> str:
    parts = [STATIC_CSS, "\n"]
    for theme in themes:
        slug = theme["id"]
        variables = theme["cssVariables"]
        if not isinstance(slug, str) or not isinstance(variables, dict):
            raise SystemExit("theme bundle is missing id or cssVariables")
        selector = (
            f"body.theme-light.omarchy-theme-{slug},\n"
            f"body.theme-dark.omarchy-theme-{slug}"
        )
        lines = [f"\t{name}: {value};" for name, value in variables.items()]
        parts.append(selector + " {\n" + "\n".join(lines) + "\n}\n\n")
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--themes",
        action="append",
        help="Directory of <slug>/colors.toml folders. Repeat to combine. Default: palettes/",
    )
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output JSON path")
    parser.add_argument("--css", default=DEFAULT_CSS, help="Output stylesheet path")
    parser.add_argument("--only", nargs="*", help="Generate only these theme ids")
    parser.add_argument("--check", action="store_true", help="Exit 1 if the outputs are stale")
    args = parser.parse_args()

    directories = args.themes if args.themes else [DEFAULT_THEMES]
    themes = [build_theme(slug, path) for slug, path in collect(directories, args.only)]
    text = bundle_text(themes)
    css = stylesheet(themes)

    if args.check:
        stale = []
        for path, expected in ((args.out, text), (args.css, css)):
            current = ""
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as handle:
                    current = handle.read()
            if current != expected:
                stale.append(os.path.relpath(path, ROOT))
        if stale:
            raise SystemExit(f"{', '.join(stale)} is stale; run python3 scripts/generate.py")
        print(f"ok {len(themes)} themes")
        return

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(text)
    with open(args.css, "w", encoding="utf-8") as handle:
        handle.write(css)
    print(f"wrote {len(themes)} themes to {os.path.relpath(args.out, ROOT)}")
    for theme in themes:
        fallbacks = theme["fallbacks"]
        note = f" ({', '.join(fallbacks)})" if isinstance(fallbacks, list) and fallbacks else ""
        print(f"  {theme['id']:<20} {theme['mode']:<5} {theme['name']}{note}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
