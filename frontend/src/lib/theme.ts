export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "planforge-theme-preference";

export function getSystemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function resolveTheme(preference: ThemePreference): "light" | "dark" {
  return preference === "system" ? getSystemTheme() : preference;
}

export function applyTheme(preference: ThemePreference): void {
  const resolved = resolveTheme(preference);
  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;
}

export function getStoredThemePreference(): ThemePreference {
  // Theme preference is stored in memory only during infrastructure phases.
  // Browser persistence is deferred until the offline/storage security gate.
  return "system";
}

export function setStoredThemePreference(preference: ThemePreference): void {
  void preference;
  void STORAGE_KEY;
}
