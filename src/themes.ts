import bundle from './themes.generated.json';

export const THEME_NONE = 'none';

export function themeClass(id: string): string {
	return `omarchy-theme-${id}`;
}

export interface AccentHsl {
	h: string;
	s: string;
	l: string;
}

export interface VivaldiColors {
	colorBg: string;
	colorAccentBg: string;
	colorWindowBg: string;
	colorFg: string;
	colorHighlightBg: string;
}

export interface Palette {
	accent: string;
	selection: string;
	muted: string;
	background: string;
	dark_background: string;
	darker_background: string;
	lighter_background: string;
	foreground: string;
	dark_foreground: string;
	light_foreground: string;
	bright_foreground: string;
	red: string;
	yellow: string;
	green: string;
	cyan: string;
	blue: string;
	magenta: string;
	bright_blue: string;
	bright_magenta: string;
}

export interface GeneratedTheme {
	id: string;
	name: string;
	mode: 'dark' | 'light';
	source: string;
	palette: Palette;
	vivaldi: VivaldiColors;
	accentHsl: AccentHsl;
	fallbacks: string[];
	cssVariables: Record<string, string>;
}

const HEX = /^#[0-9A-Fa-f]{6}$/;

function isHex(value: unknown): value is string {
	return typeof value === 'string' && HEX.test(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null;
}

function isPalette(value: unknown): value is Palette {
	if (!isRecord(value)) {
		return false;
	}
	const keys = [
		'accent',
		'selection',
		'muted',
		'background',
		'dark_background',
		'darker_background',
		'lighter_background',
		'foreground',
		'dark_foreground',
		'light_foreground',
		'bright_foreground',
		'red',
		'yellow',
		'green',
		'cyan',
		'blue',
		'magenta',
		'bright_blue',
		'bright_magenta',
	] as const;
	return keys.every((key) => isHex(value[key]));
}

function isTheme(value: unknown): value is GeneratedTheme {
	if (!isRecord(value)) {
		return false;
	}
	const accent = value['accentHsl'];
	const css = value['cssVariables'];
	const fallbacks = value['fallbacks'];
	if (!isRecord(accent) || !isRecord(css) || !Array.isArray(fallbacks)) {
		return false;
	}
	return (
		typeof value['id'] === 'string' &&
		typeof value['name'] === 'string' &&
		(value['mode'] === 'dark' || value['mode'] === 'light') &&
		typeof value['source'] === 'string' &&
		isPalette(value['palette']) &&
		typeof accent['h'] === 'string' &&
		typeof accent['s'] === 'string' &&
		typeof accent['l'] === 'string' &&
		fallbacks.every((item) => typeof item === 'string') &&
		Object.values(css).every((item) => typeof item === 'string')
	);
}

function loadThemes(value: unknown): GeneratedTheme[] {
	if (!isRecord(value) || !Array.isArray(value['themes'])) {
		throw new Error('Omarchy Themes: themes.generated.json is not a theme bundle');
	}
	const themes: GeneratedTheme[] = [];
	for (const entry of value['themes']) {
		if (!isTheme(entry)) {
			const id = isRecord(entry) && typeof entry['id'] === 'string' ? entry['id'] : 'unknown';
			throw new Error(`Omarchy Themes: theme "${id}" in the bundle is incomplete`);
		}
		themes.push(entry);
	}
	return themes;
}

export const themes: GeneratedTheme[] = loadThemes(bundle);

export function themeById(id: string): GeneratedTheme | undefined {
	return themes.find((theme) => theme.id === id);
}
