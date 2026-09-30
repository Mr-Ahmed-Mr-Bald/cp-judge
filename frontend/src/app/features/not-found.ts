import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="center-page">
      <div class="narrow stack" style="text-align: center">
        <p class="code faint">404</p>
        <h1>Page not found</h1>
        <p class="muted">
          That address does not match anything on this judge. The link may be old, or the
          problem may have been removed.
        </p>
        <div class="row" style="justify-content: center">
          <a class="btn btn-primary" routerLink="/problems">Browse problems</a>
          <a class="btn btn-ghost" routerLink="/submissions">My submissions</a>
        </div>
      </div>
    </div>
  `,
  styles: `
    .code {
      font-family: var(--font-mono);
      font-size: 3rem;
      font-weight: 800;
      margin: 0;
      opacity: 0.35;
    }
  `,
})
export class NotFoundPage {}