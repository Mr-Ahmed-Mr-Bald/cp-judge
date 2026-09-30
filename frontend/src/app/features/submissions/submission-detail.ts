import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  computed,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { toApiError } from '../../core/api-error';
import { ApiService } from '../../core/api.service';
import { ProblemDetail, SubmissionOut } from '../../core/models';
import { absoluteTime, duration, formatMs, relativeTime } from '../../core/time';
import { statusLabel, verdictInfo } from '../../core/verdict';
import { VerdictBadge } from '../../ui/verdict-badge';

/** Spec Section 7.2: re-fetch every 1 to 2 seconds until the status is DONE. */
const POLL_INTERVAL_MS = 1500;

@Component({
  selector: 'app-submission-detail',
  imports: [RouterLink, VerdictBadge],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './submission-detail.html',
  styles: `
    .head {
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .verdict-card {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1.1rem 1.25rem;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      background: var(--bg-raised);
    }

    .verdict-card .big {
      font-size: 1.6rem;
      font-weight: 800;
      letter-spacing: -0.01em;
    }

    .verdict-card .label {
      font-weight: 600;
    }

    .progress {
      height: 6px;
      border-radius: 999px;
      background: var(--bg-sunken);
      overflow: hidden;
      border: 1px solid var(--border);
    }

    .progress > div {
      height: 100%;
      background: var(--accent);
      transition: width 0.4s ease;
    }

    .progress.indeterminate > div {
      width: 35% !important;
      animation: slide 1.2s ease-in-out infinite;
    }

    @keyframes slide {
      0% {
        margin-left: -35%;
      }
      100% {
        margin-left: 100%;
      }
    }

    .facts {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 0.9rem 1.25rem;
    }

    .fact .k {
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-faint);
    }

    .fact .v {
      font-size: 0.9rem;
    }

    .code-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      padding: 0.7rem 0.9rem;
      border-bottom: 1px solid var(--border);
    }

    .code-head h2 {
      margin: 0;
      font-size: 0.95rem;
    }

    .facts-card {
      margin: 1rem 0;
    }

    .right {
      text-align: right;
    }

    .progress-note {
      margin: 0;
      font-size: 0.85rem;
    }
  `,
})
export class SubmissionDetailPage {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly formatMs = formatMs;
  protected readonly absoluteTime = absoluteTime;
  protected readonly relativeTime = relativeTime;
  protected readonly duration = duration;

  protected readonly submission = signal<SubmissionOut | null>(null);
  protected readonly problem = signal<ProblemDetail | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly notFound = signal(false);
  protected readonly live = signal(true);

  protected readonly id = computed(() => Number(this.route.snapshot.paramMap.get('id')));

  protected readonly verdict = computed(() => verdictInfo(this.submission()?.verdict));

  protected readonly isDone = computed(() => this.submission()?.status === 'DONE');

  protected readonly statusText = computed(() => {
    const submission = this.submission();
    return submission ? statusLabel(submission.status, submission.current_test) : '';
  });

  protected readonly verdictTone = computed(() => verdictInfo(this.submission()?.verdict)?.tone ?? 'neutral');

  protected readonly progressPercent = computed(() => {
    const submission = this.submission();
    if (!submission) return 0;
    if (submission.status === 'DONE') return 100;

    const total = this.problem()?.test_count ?? 0;
    const done = submission.current_test ?? 0;
    if (total <= 0) return 0;
    return Math.min(100, Math.round((done / total) * 100));
  });

  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    // Leave no timer behind when the visitor navigates away.
    this.destroyRef.onDestroy(() => this.stopPolling());
    this.load();
  }

  protected load(): void {
    const id = this.id();
    if (!Number.isFinite(id)) {
      this.notFound.set(true);
      return;
    }

    this.api.getSubmission(id).subscribe({
      next: (submission) => {
        this.submission.set(submission);
        this.error.set(null);
        this.loadProblem(slugOf(submission));
        this.schedule();
      },
      error: (error: unknown) => {
        const apiError = toApiError(error);
        this.notFound.set(apiError.status === 404);
        this.error.set(apiError.message);
        this.stopPolling();
      },
    });
  }

  /** The limits explain the verdict, so the problem is worth one extra fetch. */
  private loadProblem(slug: string): void {
    if (this.problem()?.slug === slug) return;
    this.api.getProblem(slug).subscribe({
      next: (problem) => this.problem.set(problem),
      error: () => this.problem.set(null),
    });
  }

  private schedule(): void {
    this.stopPolling();

    if (!this.live() || this.isDone() || this.submission() === null) return;

    this.timer = setTimeout(() => {
      this.timer = null;
      this.load();
    }, POLL_INTERVAL_MS);
  }

  protected stopPolling(): void {
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  protected toggleLive(): void {
    this.live.update((value) => !value);
    if (this.live()) this.schedule();
    else this.stopPolling();
  }

  protected refreshNow(): void {
    this.load();
  }

  protected copySource(source: string): void {
    void navigator.clipboard?.writeText(source);
  }
}

function slugOf(submission: SubmissionOut): string {
  return submission.problem_slug;
}