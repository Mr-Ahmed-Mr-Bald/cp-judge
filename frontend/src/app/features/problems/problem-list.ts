import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { toApiError } from '../../core/api-error';
import { ApiService } from '../../core/api.service';
import { ProblemListItem } from '../../core/models';
import { formatMs } from '../../core/time';

@Component({
  selector: 'app-problem-list',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './problem-list.html',
  styles: `
    .filters {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
      margin-bottom: 1rem;
    }

    .search {
      max-width: 20rem;
    }

    .filter-tag {
      cursor: pointer;
      border: 1px solid transparent;
      font: inherit;
      font-size: 0.78rem;
      line-height: 1.4;
    }

    .filter-tag:hover {
      border-color: var(--accent);
    }

    .filter-tag.on {
      background: var(--accent);
      color: var(--accent-text);
    }

    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.4rem;
      padding: 2.5rem 1.25rem;
      text-align: center;
    }

    .title {
      font-weight: 600;
    }

    .slug {
      display: block;
      font-size: 0.75rem;
    }

    .count {
      margin: 0.75rem 0 0;
      font-size: 0.8rem;
    }
  `,
})
export class ProblemList {
  private readonly api = inject(ApiService);

  protected readonly formatMs = formatMs;

  protected readonly problems = signal<ProblemListItem[] | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly query = signal('');
  protected readonly activeTag = signal<string | null>(null);

  /** Every tag in the catalogue, for the filter row. */
  protected readonly tags = computed(() => {
    const all = (this.problems() ?? []).flatMap((problem) => problem.tags);
    return [...new Set(all)].sort((a, b) => a.localeCompare(b));
  });

  protected readonly filtered = computed(() => {
    const problems = this.problems();
    if (!problems) return null;

    const query = this.query().trim().toLowerCase();
    const tag = this.activeTag();

    return problems.filter((problem) => {
      if (tag && !problem.tags.includes(tag)) return false;
      if (!query) return true;
      return (
        problem.title.toLowerCase().includes(query) ||
        problem.slug.toLowerCase().includes(query) ||
        problem.tags.some((value) => value.toLowerCase().includes(query))
      );
    });
  });

  constructor() {
    this.load();
  }

  protected load(): void {
    this.error.set(null);
    this.problems.set(null);
    this.api.listProblems().subscribe({
      next: (problems) => this.problems.set(problems),
      error: (error: unknown) => {
        this.error.set(toApiError(error).message);
        this.problems.set([]);
      },
    });
  }

  protected toggleTag(tag: string): void {
    this.activeTag.update((current) => (current === tag ? null : tag));
  }

  protected onQuery(value: string): void {
    this.query.set(value);
  }

  protected clearFilters(): void {
    this.query.set('');
    this.activeTag.set(null);
  }

  protected trackBySlug(_index: number, problem: ProblemListItem): string {
    return problem.slug;
  }
}
