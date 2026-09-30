import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, Router } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { ThemeService } from '../core/theme.service';

@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header class="bar">
      <div class="container inner">
        <a routerLink="/problems" class="brand">
          <span class="mark">CJ</span>
          <span class="name">CP Judge</span>
        </a>

        <nav class="nav">
          <a routerLink="/problems" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">
            Problems
          </a>
          @if (auth.isLoggedIn()) {
            <a routerLink="/submissions" routerLinkActive="active">Submissions</a>
            <a routerLink="/settings" routerLinkActive="active">Settings</a>
          }
        </nav>

        <div class="spacer"></div>

        <button
          type="button"
          class="btn btn-ghost btn-sm icon-btn"
          (click)="theme.toggle()"
          [attr.aria-label]="theme.isDark() ? 'Switch to light theme' : 'Switch to dark theme'"
          [title]="theme.isDark() ? 'Switch to light theme' : 'Switch to dark theme'"
        >
          {{ theme.isDark() ? '☾' : '☀' }}
        </button>

        @if (auth.isLoggedIn()) {
          <div class="account">
            @if (auth.isExpiringSoon()) {
              <span class="chip warn" title="Your login token is about to expire. Log in again to renew it.">
                session ending
              </span>
            }
            <a routerLink="/settings" class="handle" [title]="'Signed in as ' + auth.user()?.email">
              {{ auth.handle() }}
              @if (auth.isAdmin()) {
                <span class="role">admin</span>
              }
            </a>
            <button type="button" class="btn btn-sm" (click)="logout()">Log out</button>
          </div>
        } @else {
          <div class="account">
            <a routerLink="/login" class="btn btn-sm">Log in</a>
            <a routerLink="/register" class="btn btn-sm btn-primary">Register</a>
          </div>
        }
      </div>
    </header>
  `,
  styles: `
    .bar {
      position: sticky;
      top: 0;
      z-index: 20;
      background: color-mix(in srgb, var(--bg-raised) 88%, transparent);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--border);
    }

    .inner {
      display: flex;
      align-items: center;
      gap: 1rem;
      height: 58px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.55rem;
      color: var(--text);
      font-weight: 700;
      letter-spacing: -0.01em;
    }

    .brand:hover {
      text-decoration: none;
    }

    .mark {
      display: grid;
      place-items: center;
      width: 28px;
      height: 28px;
      border-radius: 7px;
      background: var(--accent);
      color: var(--accent-text);
      font-size: 0.72rem;
      font-weight: 800;
    }

    .nav {
      display: flex;
      gap: 0.25rem;
    }

    .nav a {
      padding: 0.35rem 0.65rem;
      border-radius: var(--radius-sm);
      color: var(--text-muted);
      font-size: 0.9rem;
      font-weight: 500;
    }

    .nav a:hover {
      background: var(--bg-hover);
      color: var(--text);
      text-decoration: none;
    }

    .nav a.active {
      color: var(--text);
      background: var(--accent-soft);
    }

    .account {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .handle {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      color: var(--text);
      font-weight: 600;
      font-size: 0.9rem;
      padding: 0.2rem 0.3rem;
      border-radius: var(--radius-sm);
    }

    .handle:hover {
      background: var(--bg-hover);
      text-decoration: none;
    }

    .role {
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--warn);
      border: 1px solid color-mix(in srgb, var(--warn) 45%, transparent);
      border-radius: 4px;
      padding: 0 0.25rem;
    }

    .chip.warn {
      color: var(--warn);
      background: var(--warn-soft);
      border-color: transparent;
    }

    .icon-btn {
      width: 32px;
      padding: 0.2rem 0;
      font-size: 1rem;
    }

    @media (max-width: 640px) {
      .name {
        display: none;
      }
    }

    /* Narrow screens: the links drop to a second row instead of squeezing
       the account controls off the edge. */
    @media (max-width: 620px) {
      .inner {
        height: auto;
        min-height: 58px;
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        flex-wrap: wrap;
        row-gap: 0.35rem;
      }

      .nav {
        order: 3;
        width: 100%;
        margin-left: -0.35rem;
      }
    }
  `,
})
export class Header {
  protected readonly auth = inject(AuthService);
  protected readonly theme = inject(ThemeService);
  private readonly router = inject(Router);

  protected logout(): void {
    this.auth.logout();
    void this.router.navigate(['/problems']);
  }
}