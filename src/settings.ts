import { type App, PluginSettingTab, Setting, type SettingDefinitionItem } from 'obsidian';
import type OmarchyThemesPlugin from './main';
import { THEME_NONE, type GeneratedTheme, themes } from './themes';

export interface SavedAccent {
	h: string;
	s: string;
	l: string;
}

export interface OmarchyThemesSettings {
	themeId: string;
	savedBaseTheme: string | null;
	savedCssTheme: string | null;
	savedAccent: SavedAccent | null;
}

export const DEFAULT_SETTINGS: OmarchyThemesSettings = {
	themeId: THEME_NONE,
	savedBaseTheme: null,
	savedCssTheme: null,
	savedAccent: null,
};

const THEME_DESC =
	'Applies straight away and stays selected after a restart. Choose none to restore the previous appearance. Light themes use light mode and dark themes use dark mode. A theme from the appearance settings is turned off until you choose none.';

const SWATCHES: readonly (readonly [string, keyof GeneratedTheme['palette']])[] = [
	['Background', 'background'],
	['Tab bar', 'dark_background'],
	['Text', 'foreground'],
	['Accent', 'accent'],
];

export class OmarchySettingTab extends PluginSettingTab {
	plugin: OmarchyThemesPlugin;

	constructor(app: App, plugin: OmarchyThemesPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	getSettingDefinitions(): SettingDefinitionItem[] {
		return [
			{
				name: 'Theme',
				desc: THEME_DESC,
				render: (setting: Setting) => {
					this.addThemeControl(setting);
				},
			},
		];
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();
		const setting = new Setting(containerEl).setName('Theme').setDesc(THEME_DESC);
		this.addThemeControl(setting);
	}

	override getControlValue(key: string): unknown {
		if (key === 'themeId') {
			return this.plugin.settings.themeId;
		}
		return undefined;
	}

	override setControlValue(key: string, value: unknown): void {
		if (key === 'themeId' && typeof value === 'string') {
			void this.plugin.setTheme(value);
		}
	}

	private addThemeControl(setting: Setting): void {
		const ordered = [...themes].sort((left, right) => left.name.localeCompare(right.name));
		const swatchRow = setting.settingEl.createDiv({ cls: 'omarchy-swatches' });
		setting.addDropdown((dropdown) => {
			dropdown.addOption(THEME_NONE, 'None / off');
			for (const theme of ordered) {
				dropdown.addOption(theme.id, theme.name);
			}
			dropdown.setValue(this.plugin.settings.themeId);
			dropdown.onChange(async (value) => {
				await this.plugin.setTheme(value);
				this.drawSwatches(swatchRow);
			});
		});
		this.drawSwatches(swatchRow);
	}

	private drawSwatches(row: HTMLElement): void {
		row.empty();
		const theme = this.plugin.activeTheme();
		if (!theme) {
			return;
		}
		for (const [label, key] of SWATCHES) {
			const color = theme.palette[key];
			const swatch = row.createDiv({ cls: 'omarchy-swatch' });
			swatch.style.backgroundColor = color;
			swatch.setAttr('title', `${label} ${color}`);
			swatch.setAttr('aria-label', `${label} ${color}`);
		}
	}
}
