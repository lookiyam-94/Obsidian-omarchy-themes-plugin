import { Notice, Plugin } from 'obsidian';
import { DEFAULT_SETTINGS, type OmarchyThemesSettings, OmarchySettingTab, type SavedAccent } from './settings';
import { THEME_NONE, type GeneratedTheme, themeById, themeClass, themes } from './themes';
import { baseThemeFor, readBaseTheme, readCssTheme, writeVaultConfig } from './vault-config';

const ACCENT_PROPS = ['--accent-h', '--accent-s', '--accent-l'] as const;

export default class OmarchyThemesPlugin extends Plugin {
	settings: OmarchyThemesSettings = DEFAULT_SETTINGS;
	private statusEl: HTMLElement | null = null;
	private applying = false;
	private unloaded = false;

	async onload(): Promise<void> {
		await this.loadSettings();
		this.statusEl = this.addStatusBarItem();
		this.addSettingTab(new OmarchySettingTab(this.app, this));
		this.registerEvent(this.app.workspace.on('css-change', () => this.onCssChange()));
		this.register(() => this.removePaint());
		this.applyCurrent();
		this.app.workspace.onLayoutReady(() => {
			if (!this.unloaded) {
				this.applyCurrent();
			}
		});
	}

	onunload(): void {
		this.unloaded = true;
		this.removePaint();
		this.restoreSavedAppearance();
	}

	activeTheme(): GeneratedTheme | null {
		if (this.settings.themeId === THEME_NONE) {
			return null;
		}
		return themeById(this.settings.themeId) ?? null;
	}

	async setTheme(themeId: string): Promise<void> {
		if (themeId === THEME_NONE) {
			this.settings.themeId = THEME_NONE;
			this.removePaint();
			this.restoreSavedAppearance();
			this.settings.savedBaseTheme = null;
			this.settings.savedCssTheme = null;
			this.settings.savedAccent = null;
			await this.saveSettings();
			this.refreshStatus();
			return;
		}

		const theme = themeById(themeId);
		if (!theme) {
			new Notice(`Omarchy Themes: unknown theme "${themeId}".`);
			return;
		}

		if (this.settings.savedBaseTheme === null) {
			this.settings.savedBaseTheme = readBaseTheme(this.app);
			this.settings.savedCssTheme = readCssTheme(this.app);
			this.settings.savedAccent = readInlineAccent();
		}
		this.settings.themeId = theme.id;
		await this.saveSettings();
		this.applyCurrent();
	}

	private async loadSettings(): Promise<void> {
		const stored = (await this.loadData()) as Partial<OmarchyThemesSettings> | null;
		this.settings = Object.assign({}, DEFAULT_SETTINGS, stored);
		let dirty = false;
		if (this.settings.themeId !== THEME_NONE && !themeById(this.settings.themeId)) {
			new Notice(`Omarchy Themes: "${this.settings.themeId}" is not in this version. Switched off.`);
			this.settings.themeId = THEME_NONE;
			dirty = true;
		}
		if (this.settings.themeId === THEME_NONE && this.settings.savedBaseTheme !== null) {
			this.restoreSavedAppearance();
			this.settings.savedBaseTheme = null;
			this.settings.savedCssTheme = null;
			this.settings.savedAccent = null;
			dirty = true;
		}
		if (dirty) {
			await this.saveSettings();
		}
	}

	private async saveSettings(): Promise<void> {
		await this.saveData(this.settings);
	}

	private onCssChange(): void {
		if (this.unloaded || this.settings.themeId === THEME_NONE) {
			return;
		}
		const theme = this.activeTheme();
		if (!theme) {
			return;
		}
		this.paint(theme);
		writeInlineAccent(theme.accentHsl);
		if (!this.applying) {
			this.applyBaseMode(theme);
		}
	}

	private applyCurrent(): void {
		if (this.unloaded) {
			return;
		}
		const theme = this.activeTheme();
		if (!theme) {
			this.removePaint();
			this.refreshStatus();
			return;
		}
		this.paint(theme);
		this.applyBaseMode(theme);
		writeInlineAccent(theme.accentHsl);
		this.refreshStatus();
	}

	private applyBaseMode(theme: GeneratedTheme): void {
		this.applying = true;
		try {
			const desired = baseThemeFor(theme.mode);
			if (readBaseTheme(this.app) !== desired) {
				writeVaultConfig(this.app, 'theme', desired);
			}
			if (readCssTheme(this.app) !== '') {
				writeVaultConfig(this.app, 'cssTheme', '');
			}
			document.body.addClass(themeClass(theme.id));
		} finally {
			this.applying = false;
		}
	}

	private paint(theme: GeneratedTheme): void {
		this.clearThemeClasses();
		document.body.addClass(themeClass(theme.id));
	}

	private clearThemeClasses(): void {
		for (const theme of themes) {
			document.body.removeClass(themeClass(theme.id));
		}
	}

	private removePaint(): void {
		this.clearThemeClasses();
	}

	private restoreSavedAppearance(): void {
		if (this.settings.savedBaseTheme !== null) {
			writeVaultConfig(this.app, 'theme', this.settings.savedBaseTheme);
		}
		if (this.settings.savedCssTheme !== null) {
			writeVaultConfig(this.app, 'cssTheme', this.settings.savedCssTheme);
		}
		restoreInlineAccent(this.settings.savedAccent);
	}

	private refreshStatus(): void {
		const theme = this.activeTheme();
		this.statusEl?.setText(theme ? theme.name : '');
	}
}

function readInlineAccent(): SavedAccent {
	return {
		h: document.body.style.getPropertyValue('--accent-h'),
		s: document.body.style.getPropertyValue('--accent-s'),
		l: document.body.style.getPropertyValue('--accent-l'),
	};
}

function writeInlineAccent(accent: SavedAccent): void {
	document.body.style.setProperty('--accent-h', accent.h);
	document.body.style.setProperty('--accent-s', accent.s);
	document.body.style.setProperty('--accent-l', accent.l);
}

function accentKey(prop: (typeof ACCENT_PROPS)[number]): keyof SavedAccent {
	switch (prop) {
		case '--accent-h':
			return 'h';
		case '--accent-s':
			return 's';
		case '--accent-l':
			return 'l';
		default: {
			const unreachable: never = prop;
			return unreachable;
		}
	}
}

function restoreInlineAccent(accent: SavedAccent | null): void {
	if (!accent) {
		return;
	}
	for (const prop of ACCENT_PROPS) {
		const value = accent[accentKey(prop)];
		if (value) {
			document.body.style.setProperty(prop, value);
		} else {
			document.body.style.removeProperty(prop);
		}
	}
}
