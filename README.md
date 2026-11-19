# Omarchy themes for Obsidian

Omarchy themes for Obsidian. Pick one in the plugin settings and the vault uses that palette. This is for a computer that does not run Omarchy, such as a Windows work laptop, where nothing else switches the theme for you.

The colours come from the same `colors.toml` files as [omarchy-vivaldi-themes](https://github.com/lookiyam-94/omarchy-vivaldi-themes), and the four main roles are mapped the same way:

| Obsidian | Omarchy key | Vivaldi field |
| --- | --- | --- |
| Main background | `background` | Background (`colorBg`) |
| Tab bar, title bar, ribbon, status bar | `dark_background` | Tab bar and window (`colorAccentBg`, `colorWindowBg`) |
| Text | `foreground` | Foreground (`colorFg`) |
| Accent, links, focus, text selection | `accent` | Highlight (`colorHighlightBg`) |

Headings, code, borders, and the other interface colours use further keys from that same file (`darker_background`, `lighter_background`, `selection`, `muted`, `blue`, `green`, and the rest). The plugin does not invent new hex values.

## Install

Copy three files into the vault. The folder name has to be `omarchy-themes`.

1. Open the vault folder in File Explorer.
2. Open `.obsidian`, then `plugins`. Create `plugins` if it is not there.
3. Create a folder named `omarchy-themes`.
4. Copy `main.js`, `manifest.json`, and `styles.css` from this repository into that folder.
5. In Obsidian, open Settings → Community plugins. Turn Restricted mode off if it is on. Click the reload button, then turn on **Omarchy Themes**.

`main.js` in this repository is already built, so you do not need Node to install it.

## Use

Open Settings → Omarchy Themes and pick a theme. Obsidian updates immediately. The choice is still selected after you quit and open Obsidian again.

A light theme switches Obsidian to light mode. A dark theme switches it to dark mode. While one of these themes is selected, an appearance theme you had installed under Settings → Appearance is turned off, so it does not paint over these colours. It comes back when you pick **None / off**. That option also restores the light or dark mode you were using before.

The status bar shows the theme name while one is selected.

## Themes

26 themes. Five are light: Catppuccin Latte, Flexoki Light, Lupine, Rose Pine, and White. The rest are dark.

Catppuccin, Catppuccin Latte, Ethereal, Everforest, Flexoki Light, Gruvbox, Hackerman, Kanagawa, Last Horizon, Lumon, Lupine, Matte Black, Miasma, Nord, Osaka Jade, Retro-82, Ristretto, Rose Pine, Solitude, Tokyo Night, Vantablack, and White are from Omarchy 4.0.4. Jade Horse is from Omarchy 4.5.0. Starship is the palette from the current Omarchy tree, the same one the Vivaldi repo used. Dracula and Rose Pine Dark are the community themes already included with the Vivaldi themes ([catlee/omarchy-dracula-theme](https://github.com/catlee/omarchy-dracula-theme) and [guilhermetk/omarchy-rose-pine-dark](https://github.com/guilhermetk/omarchy-rose-pine-dark)).

Osaka Jade shipped in Omarchy 4.0.4. The current Omarchy default branch does not include it. It is here because the Vivaldi catalogue still has it.

Last Horizon, Solitude, and White do not define `orange` or `brown`. Slots that ask for orange use that theme's `yellow`.

## Regenerate

`palettes/<theme-id>/colors.toml` is the input. The generator writes `src/themes.generated.json`, which the plugin bundles, and `styles.css`, which Obsidian loads.

```bash
python3 scripts/generate.py
npm run build
```

Check the result against the Vivaldi theme zips:

```bash
python3 scripts/check_colors.py
```

To build from an Omarchy install instead of the bundled palettes:

```bash
python3 scripts/generate.py --themes /usr/share/omarchy/themes
```

A folder is included when it contains `colors.toml`. To add a theme, put `palettes/<theme-id>/colors.toml` in place and run the generator again. Pass `--themes` more than once to combine directories. `--only nord tokyo-night` limits the run. `--check` exits with an error if the generated file is out of date.

## Plan

This version:

- Bundles the 26 themes above.
- Adds a settings tab with those themes and **None / off**.
- Applies the choice immediately and stores it.
- Sets Obsidian's light or dark mode from the palette.
- Generates the theme data from `colors.toml`.
- Checks those colours against the Vivaldi themes.
- Builds the plugin on pull requests.

Next:

- A GitHub Actions release workflow that attaches `main.js`, `manifest.json`, and `styles.css` to a release. That is the zip the community plugin list installs.
- Submit the plugin to the Obsidian community plugin directory.
- Rebuild `palettes/` when Omarchy adds or changes a theme.

The palettes belong to their authors. This repository repackages them for Obsidian. The plugin and the generator are MIT licensed. Unofficial, and not affiliated with Omarchy or Obsidian.
