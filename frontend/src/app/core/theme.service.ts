import { DOCUMENT } from '@angular/common';
import { Injectable, computed, inject, signal } from '@angular/core';

export type Theme = 'dark' | 'light';

const THEME_KEY = 'cpjudge.theme';

/**
 * Two palettes driven by CSS custom properties on <html data-theme>. Dark is
 * the default because statement pages with maths read better that way.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly _theme = signal<Theme>(readStoredTheme());

  readonly theme = this._theme.asReadonly();
  readonly isDark = computed(() => this._theme() === 'dark');

  apply(): void {
    this.document.documentElement.setAttribute('data-theme', this._theme());
  }

  toggle(): void {
    this._theme.update((theme) => (theme === 'dark' ? 'light' : 'dark'));
    localStorage.setItem(THEME_KEY, this._theme());
    this.apply();
  }
}

function readStoredTheme(): Theme {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === 'dark' || stored === 'light') return stored;
  return 'dark';
}