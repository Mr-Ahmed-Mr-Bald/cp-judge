import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { toApiError } from '../../core/api-error';
import { ApiService } from '../../core/api.service';
import { ProblemListItem, SubmissionListItem } from '../../core/models';
import { absoluteTime, duration, relativeTime } from '../../core/time';
import { statusLabel } from '../../core/verdict';
import { VerdictBadge } from '../../ui/verdict-badge';

/** Matches the submission page: keep the list fresh while work is in flight. */
const REFRESH_INTERVAL_MS = 2000;

@Component({
  selector: 'app-my-submissions',
  imports: [RouterLink, VerdictBadge],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './my-submissions.html',
  styles: `
    .filters {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
      margin-bottom: 1rem;
    }

    .filters select {
      max-width: 22rem;
    }

    .problem-link {
      font-weight: 600;
    }

    .id-cell {
      font-family: var(--font-mono);
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .pending {
      color: var(--text-muted);
      font-size: 0.85rem;
    }

    .test {
      margin-left: 0.45rem;
      font-size: 0.78rem;
    }

    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.4rem;
      padding: 2.5rem 1.25rem;
      text-align: center;
    }
  `,
})
export class MySubmissionsPage {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly absoluteTime = absoluteTime;
  protected readonly relativeTime = relativeTime;
  protected readonly duration = duration;

  protected readonly submissions = signal<SubmissionListItem[] | null>(null);
  protected readonly problems = signal<ProblemListItem[]>([]);
  protected readonly error = signal<string | null>(null);

  /** Written to the URL so a filtered view survives a reload or a shared link. */
  protected readonly problemSlug = signal<string>(
    this.route.snapshot.queryParamMap.get('problem') ?? '',
  );


  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.destroyRef.onDestroy(() => this.stopPolling());
    this.api.listProblems().subscribe({
      next: (problems) => this.problems.set(problems),
      error: () => this.problems.set([]),
    });
    this.load();
  }

  protected load(): void {
    this.api.listSubmissions(this.problemSlug() || undefined, 50).subscribe({
      next: (submissions) => {
        this.submissions.set(submissions);
        this.error.set(null);
        this.schedule();
      },
      error: (error: unknown) => {
        this.error.set(toApiError(error).message);
        this.submissions.set([]);
        this.stopPolling();
      },
    });
  }

  /** Refresh quietly: a failing background poll must not blank the table. */
  private refresh(): void {
    this.api.listSubmissions(this.problemSlug() || undefined, 50).subscribe({
      next: (submissions) => {
        this.submissions.set(submissions);
        this.schedule();
      },
      error: () => this.stopPolling(),
    });
  }

  private schedule(): void {
    this.stopPolling();
    const rows = this.submissions() ?? [];
    const busy = rows.some((row) => row.status !== 'DONE');
    if (!busy) return;

    this.timer = setTimeout(() => {
      this.timer = null;
      this.refresh();
    }, REFRESH_INTERVAL_MS);
  }

  private stopPolling(): void {
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  protected filterLabel(): string {
    const slug = this.problemSlug();
    return this.problems().find((problem) => problem.slug === slug)?.title ?? slug;
  }

  protected onFilterChange(value: string): void {
    this.problemSlug.set(value);
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: value ? { problem: value } : {},
      replaceUrl: true,
    });
    // Ask the server rather than filtering locally: the endpoint applies the
    // filter before the limit, so this shows the newest matches.
    this.submissions.set(null);
    this.load();
  }

  protected statusLabel(submission: SubmissionListItem): string {
    return statusLabel(submission.status, null);
  }
}