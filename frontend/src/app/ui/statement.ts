import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { DomSanitizer, type SafeHtml } from '@angular/platform-browser';
import { MarkdownService } from '../core/markdown.service';

/**
 * Renders a statement: Markdown with $...$ / $$...$$ math through KaTeX.
 * The HTML is produced by MarkdownService, which escapes raw HTML from the
 * source first, and is trusted here for that reason.
 */
@Component({
  selector: 'app-statement',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div class="statement" [innerHTML]="html()"></div>`,
})
export class Statement {
  private readonly markdown = inject(MarkdownService);
  private readonly sanitizer = inject(DomSanitizer);

  readonly markdownSource = input.required<string>();

  protected readonly html = computed<SafeHtml>(() =>
    this.sanitizer.bypassSecurityTrustHtml(this.markdown.render(this.markdownSource())),
  );
}