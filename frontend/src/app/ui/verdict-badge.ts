import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { Verdict } from '../core/models';
import { verdictInfo } from '../core/verdict';

@Component({
  selector: 'app-verdict-badge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (info(); as badge) {
      <span class="badge" [class]="'badge tone-' + badge.tone" [title]="badge.hint">
        <span class="code">{{ verdict() }}</span>
        @if (!compact()) {
          <span class="label">{{ badge.label }}</span>
        }
      </span>
    } @else {
      <span class="badge tone-pending" title="Not judged yet">
        <span class="label">Pending</span>
      </span>
    }
  `,
  styles: `
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 600;
      white-space: nowrap;
      border: 1px solid transparent;
    }

    .code {
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.03em;
    }

    .tone-ok {
      background: var(--ok-soft);
      color: var(--ok);
    }

    .tone-bad {
      background: var(--bad-soft);
      color: var(--bad);
    }

    .tone-warn {
      background: var(--warn-soft);
      color: var(--warn);
    }

    .tone-neutral {
      background: var(--neutral-soft);
      color: var(--neutral);
    }

    .tone-pending {
      background: var(--bg-sunken);
      color: var(--text-muted);
      border-color: var(--border);
    }
  `,
})
export class VerdictBadge {
  readonly verdict = input.required<Verdict | null>();
  /** Shows only the two-letter code, for dense tables. */
  readonly compact = input(false);

  protected readonly info = computed(() => verdictInfo(this.verdict()));
}