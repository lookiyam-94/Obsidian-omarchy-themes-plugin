import { type App } from 'obsidian';

/**
 * Obsidian's own settings tabs call vault.getConfig and vault.setConfig.
 * Those methods are not on the published Vault type.
 */
interface VaultWithConfig {
	getConfig(key: string): unknown;
	setConfig(key: string, value: unknown): void;
}

function vault(app: App): VaultWithConfig {
	return app.vault as unknown as VaultWithConfig;
}

export function readVaultConfig(app: App, key: string): unknown {
	return vault(app).getConfig(key);
}

export function writeVaultConfig(app: App, key: string, value: unknown): void {
	vault(app).setConfig(key, value);
}

export function readBaseTheme(app: App): string {
	const value = readVaultConfig(app, 'theme');
	if (value === 'obsidian' || value === 'moonstone' || value === 'system') {
		return value;
	}
	return 'system';
}

export function readCssTheme(app: App): string {
	const value = readVaultConfig(app, 'cssTheme');
	return typeof value === 'string' ? value : '';
}

export function baseThemeFor(mode: 'dark' | 'light'): 'obsidian' | 'moonstone' {
	switch (mode) {
		case 'dark':
			return 'obsidian';
		case 'light':
			return 'moonstone';
		default: {
			const unreachable: never = mode;
			return unreachable;
		}
	}
}
