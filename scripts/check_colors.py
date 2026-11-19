#!/usr/bin/env python3
"""Check generated colours against the Vivaldi theme archives.

Downloads each theme zip from lookiyam-94/omarchy-vivaldi-themes and compares
settings.json with the generated bundle.

    python3 scripts/check_colors.py
    python3 scripts/check_colors.py --settings /path/to/extracted-settings
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED = os.path.join(ROOT, "src", "themes.generated.json")
VIVALDI_API = "https://api.github.com/repos/lookiyam-94/omarchy-vivaldi-themes/contents/themes"
VIVALDI_ZIP = "https://raw.githubusercontent.com/lookiyam-94/omarchy-vivaldi-themes/main/themes/{slug}.zip"

# Mode column from the Vivaldi repo README.
README_MODES = {
    "catppuccin-latte": "light",
    "catppuccin": "dark",
    "dracula": "dark",
    "ethereal": "dark",
    "everforest": "dark",
    "flexoki-light": "light",
    "gruvbox": "dark",
    "hackerman": "dark",
    "jade-horse": "dark",
    "kanagawa": "dark",
    "last-horizon": "dark",
    "lumon": "dark",
    "lupine": "light",
    "matte-black": "dark",
    "miasma": "dark",
    "nord": "dark",
    "osaka-jade": "dark",
    "retro-82": "dark",
    "ristretto": "dark",
    "rose-pine": "light",
    "rose-pine-dark": "dark",
    "solitude": "dark",
    "starship": "dark",
    "tokyo-night": "dark",
    "vantablack": "dark",
    "white": "light",
}

VIVALDI_CSS = {
    "colorBg": ("--background-primary",),
    "colorAccentBg": (
        "--background-secondary",
        "--titlebar-background",
        "--titlebar-background-focused",
        "--tab-container-background",
        "--ribbon-background",
        "--status-bar-background",
    ),
    "colorWindowBg": ("--titlebar-background",),
    "colorFg": ("--text-normal",),
    "colorHighlightBg": (
        "--interactive-accent",
        "--interactive-accent-hover",
        "--text-accent",
        "--text-accent-hover",
        "--text-selection",
        "--text-highlight-bg",
        "--color-accent",
        "--link-color",
        "--caret-color",
    ),
}

PALETTE_FIELDS = {
    "colorBg": "background",
    "colorAccentBg": "dark_background",
    "colorWindowBg": "dark_background",
    "colorFg": "foreground",
    "colorHighlightBg": "accent",
}

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
RGB_RE = re.compile(r"^\d+, \d+, \d+$")
HSL_RE = re.compile(r"^\d+, \d+%, \d+%$")


def fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "omarchy-themes-check",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "omarchy-themes-check"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def vivaldi_slugs() -> list[str]:
    payload = fetch_json(VIVALDI_API)
    if not isinstance(payload, list):
        raise SystemExit("unexpected theme listing from the Vivaldi repo")
    slugs: list[str] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if isinstance(name, str) and name.endswith(".zip"):
            slugs.append(name[:-4])
    return sorted(slugs)


def settings_from_zip(slug: str) -> dict[str, object]:
    blob = fetch_bytes(VIVALDI_ZIP.format(slug=slug))
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        raw = json.loads(archive.read("settings.json"))
    if not isinstance(raw, dict):
        raise SystemExit(f"{slug}: settings.json is not an object")
    return raw


def settings_from_dir(directory: str, slug: str) -> dict[str, object]:
    path = os.path.join(directory, slug + ".json")
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise SystemExit(f"{path} is not an object")
    return raw


def rgb_of(hex_color: str) -> str:
    raw = hex_color[1:]
    return f"{int(raw[0:2], 16)}, {int(raw[2:4], 16)}, {int(raw[4:6], 16)}"


def check_theme(theme: dict[str, object], settings: dict[str, object], failures: list[str]) -> None:
    slug = str(theme["id"])
    palette = theme["palette"]
    css = theme["cssVariables"]
    vivaldi = theme["vivaldi"]
    if not isinstance(palette, dict) or not isinstance(css, dict) or not isinstance(vivaldi, dict):
        failures.append(f"{slug}: bundle shape is wrong")
        return

    expected_mode = README_MODES.get(slug)
    if expected_mode is None:
        failures.append(f"{slug}: not in the Vivaldi README mode table")
    elif theme.get("mode") != expected_mode:
        failures.append(f"{slug}: mode is {theme.get('mode')}, Vivaldi README says {expected_mode}")

    for field, palette_key in PALETTE_FIELDS.items():
        expected = settings.get(field)
        got_palette = palette.get(palette_key)
        got_vivaldi = vivaldi.get(field)
        if got_palette != expected:
            failures.append(f"{slug}: palette {palette_key} is {got_palette!r}, Vivaldi {field} is {expected!r}")
        if got_vivaldi != expected:
            failures.append(f"{slug}: recorded {field} is {got_vivaldi!r}, Vivaldi settings say {expected!r}")

    for field, variables in VIVALDI_CSS.items():
        expected = settings.get(field)
        for variable in variables:
            got = css.get(variable)
            if got != expected:
                failures.append(f"{slug}: {variable} is {got!r}, Vivaldi {field} is {expected!r}")

    css_path = os.path.join(ROOT, "styles.css")
    with open(css_path, encoding="utf-8") as handle:
        stylesheet = handle.read()
    block = re.search(
        rf"body\.theme-dark\.omarchy-theme-{re.escape(slug)} \{{(.*?)\n\}}",
        stylesheet,
        re.S,
    )
    if block is None:
        failures.append(f"{slug}: styles.css has no rule for omarchy-theme-{slug}")
    else:
        background = css.get("--background-primary")
        if f"--background-primary: {background};" not in block.group(1):
            failures.append(f"{slug}: styles.css background does not match the bundle")

    palette_hex = {value for value in palette.values() if isinstance(value, str)}
    palette_rgb = {rgb_of(value) for value in palette_hex if HEX_RE.match(value)}
    accent = palette.get("accent")
    for variable, value in css.items():
        if not isinstance(value, str):
            failures.append(f"{slug}: {variable} is not a string")
            continue
        if HEX_RE.match(value):
            if value not in palette_hex:
                failures.append(f"{slug}: {variable} {value} is not a colors.toml colour")
            continue
        if RGB_RE.match(value):
            if value not in palette_rgb:
                failures.append(f"{slug}: {variable} {value} is not the RGB of a colors.toml colour")
            continue
        if variable == "--interactive-accent-hsl" and isinstance(accent, str) and HSL_RE.match(value):
            continue
        failures.append(f"{slug}: {variable} has unexpected value {value!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--settings", help="Directory of <slug>.json files already extracted from the Vivaldi zips")
    parser.add_argument("--generated", default=GENERATED)
    args = parser.parse_args()

    with open(args.generated, encoding="utf-8") as handle:
        bundle = json.load(handle)
    themes = bundle["themes"]
    by_id = {theme["id"]: theme for theme in themes}

    if args.settings:
        slugs = sorted(name[:-5] for name in os.listdir(args.settings) if name.endswith(".json"))
    else:
        slugs = vivaldi_slugs()

    failures: list[str] = []
    generated_ids = sorted(by_id)
    if generated_ids != slugs:
        missing = sorted(set(slugs) - set(generated_ids))
        extra = sorted(set(generated_ids) - set(slugs))
        if missing:
            failures.append("missing from the bundle: " + ", ".join(missing))
        if extra:
            failures.append("not in the Vivaldi repo: " + ", ".join(extra))

    names: list[str] = []
    for slug in slugs:
        theme = by_id.get(slug)
        if theme is None:
            continue
        if args.settings:
            settings = settings_from_dir(args.settings, slug)
        else:
            print(f"fetch {slug}", flush=True)
            settings = settings_from_zip(slug)
        check_theme(theme, settings, failures)
        names.append(f"{theme['name']} ({theme['mode']})")

    if failures:
        print(f"FAIL {len(failures)}", file=sys.stderr)
        for failure in failures:
            print(failure, file=sys.stderr)
        raise SystemExit(1)

    print(f"OK {len(slugs)} themes match the Vivaldi colours")
    for name in names:
        print(f"  {name}")


if __name__ == "__main__":
    main()
