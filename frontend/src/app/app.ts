import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Header } from './ui/header';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-header />
    <main>
      <router-outlet />
    </main>
    <footer class="foot">
      <div class="container">
        <span class="faint">C++17 · judged in Docker sandboxes · one submission at a time</span>
      </div>
    </footer>
  `,
  styles: `
    main {
      min-height: calc(100vh - 58px - 52px);
    }

    .foot {
      border-top: 1px solid var(--border);
      padding: 1rem 0;
      font-size: 0.8rem;
    }
  `,
})
export class App {}