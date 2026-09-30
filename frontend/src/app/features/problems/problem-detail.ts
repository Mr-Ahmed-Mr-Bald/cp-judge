import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { toApiError } from '../../core/api-error';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ProblemDetail, SOURCE_MAX_BYTES, SubmissionListItem } from '../../core/models';
import { Statement } from '../../ui/statement';
import { VerdictBadge } from '../../ui/verdict-badge';
import { formatMs, relativeTime } from '../../core/time';

const DRAFT_PREFIX = 'cpjudge.draft.';
const DRAFT_SAMPLE = `#include <iostream>
using namespace std;

int main() {
  ios::sync_with_stdio(false);
  cin.tie(nullptr);

  // Read, solve, print.
  return 0;
}
`;

@Component({
  selector: 'app-problem-detail',
  imports: [FormsModule, RouterLink, Statement, VerdictBadge],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './problem-detail.html',
  styles: `
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(340px, 1fr);
      gap: 1.5rem;
      align-items: start;
    }

    @media (max-width: 940px) {
      .layout {
        grid-template-columns: minmax(0, 1fr);
      }
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-bottom: 1.25rem;
    }

    .editor-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      padding: 0.7rem 0.9rem;
      border-bottom: 1px solid var(--border);
    }

    .editor-head h2 {
      margin: 0;
      font-size: 0.95rem;
    }

    textarea {
      border: none;
      border-radius: 0;
      min-height: 22rem;
    }

    textarea:focus {
      box-shadow: none;
    }

    .editor-foot {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      padding: 0.7rem 0.9rem;
      border-top: 1px solid var(--border);
    }

    .recent {
      margin-top: 1.5rem;
    }

    .recent h2 {
      font-size: 0.95rem;
      margin-bottom: 0.6rem;
    }

    .none {
      margin: 0;
      font-size: 0.88rem;
    }

    .all {
      margin: 0.7rem 0 0;
      font-size: 0.82rem;
    }

    .over {
      color: var(--bad);
      font-weight: 600;
    }

    .recent-list {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .recent-row {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.45rem 0.7rem;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: var(--bg-sunken);
      font-size: 0.85rem;
    }

    .recent-row:hover {
      background: var(--bg-hover);
      text-decoration: none;
    }
  `,
})
export class ProblemDetailPage {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  protected readonly auth = inject(AuthService);

  protected readonly formatMs = formatMs;
  protected readonly relativeTime = relativeTime;
  protected readonly maxBytes = SOURCE_MAX_BYTES;

  protected readonly problem = signal<ProblemDetail | null>(null);
  protected readonly loadError = signal<string | null>(null);
  protected readonly notFound = signal(false);

  /** A signal, not a plain field: canSubmit() is a computed over it. */
  protected readonly sourceCode = signal('');
  protected readonly submitting = signal(false);
  protected readonly submitError = signal<string | null>(null);

  /** The user's last few submissions to this problem, for context. */
  protected readonly recent = signal<SubmissionListItem[] | null>(null);

  protected readonly sourceBytes = computed(() =>
    new TextEncoder().encode(this.sourceCode()).length,
  );
  protected readonly overLimit = computed(() => this.sourceBytes() > SOURCE_MAX_BYTES);
  protected readonly canSubmit = computed(
    () =>
      this.auth.isLoggedIn() &&
      !this.submitting() &&
      this.sourceCode().trim().length > 0 &&
      !this.overLimit() &&
      this.problem() !== null,
  );

  constructor() {
    const slug = this.route.snapshot.paramMap.get('slug') ?? '';
    this.load(slug);
  }

  protected load(slug: string): void {
    this.problem.set(null);
    this.notFound.set(false);
    this.loadError.set(null);

    this.api.getProblem(slug).subscribe({
      next: (problem) => {
        this.problem.set(problem);
        this.sourceCode.set(readDraft(slug));
        this.loadRecent(slug);
      },
      error: (error: unknown) => {
        const apiError = toApiError(error);
        this.notFound.set(apiError.status === 404);
        this.loadError.set(apiError.message);
      },
    });
  }

  private loadRecent(slug: string): void {
    if (!this.auth.isLoggedIn()) {
      this.recent.set(null);
      return;
    }
    this.recent.set(null);
    this.api.listSubmissions(slug, 5).subscribe({
      next: (submissions) => this.recent.set(submissions),
      error: () => this.recent.set([]),
    });
  }

  /** Drafts survive reloads so a half-written solution is never lost. */
  protected onSourceChange(value: string): void {
    this.sourceCode.set(value);
    this.submitError.set(null);
    const slug = this.problem()?.slug;
    if (slug) localStorage.setItem(DRAFT_PREFIX + slug, value);
  }

  protected resetToTemplate(): void {
    this.onSourceChange(DRAFT_SAMPLE);
  }

  protected clearDraft(): void {
    const slug = this.problem()?.slug;
    if (slug) localStorage.removeItem(DRAFT_PREFIX + slug);
    this.sourceCode.set('');
  }

  protected onTab(event: KeyboardEvent, textarea: HTMLTextAreaElement): void {
    if (event.key !== 'Tab') return;
    event.preventDefault();
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const source = this.sourceCode();
    const next = `${source.slice(0, start)}  ${source.slice(end)}`;
    this.onSourceChange(next);
    queueMicrotask(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 2;
    });
  }

  protected async submit(): Promise<void> {
    const problem = this.problem();
    if (!problem || !this.canSubmit()) return;

    this.submitting.set(true);
    this.submitError.set(null);

    try {
      const submission = await firstValueFrom(this.api.submit(problem.slug, this.sourceCode()));

      await this.router.navigate(['/submissions', submission.id]);
    } catch (failure) {
      this.submitError.set(toApiError(failure).message);
    } finally {
      this.submitting.set(false);
    }
  }
}

function readDraft(slug: string): string {
  return localStorage.getItem(DRAFT_PREFIX + slug) ?? DRAFT_SAMPLE;
}