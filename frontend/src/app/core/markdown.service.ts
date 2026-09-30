import { Injectable } from '@angular/core';
import katex from 'katex';
import { Marked, Renderer, type Tokens } from 'marked';

/**
 * Statements are Markdown with LaTeX between $...$ (inline) and $$...$$
 * (display), per spec Section 5.2. marked renders the Markdown, these two
 * extensions render the math with KaTeX.
 */

/** $...$ on a single line. A trailing digit is excluded so "$5 and $6" stays text. */
const INLINE_MATH = /^\$(?!\s)((?:\\\$|[^$\n])+?)(?<!\s)\$(?!\d)/;

/** $$...$$ on its own lines, or inline when a statement uses a one-liner. */
const BLOCK_MATH = /^\$\$([\s\S]+?)\$\$(?:\n+|$)/;

const PLACEHOLDER = (index: number) => `%%CJCODE${index}%%`;

@Injectable({ providedIn: 'root' })
export class MarkdownService {
  private readonly marked: Marked;

  constructor() {
    const renderer = new Renderer();

    renderer.code = ({ text, lang }: Tokens.Code) => {
      const language = lang ? ` class="language-${escapeHtml(lang)}"` : '';
      return `<pre><code${language}>${escapeHtml(text)}</code></pre>\n`;
    };

    renderer.codespan = ({ text }: Tokens.Codespan) => `<code>${escapeHtml(text)}</code>`;

    this.marked = new Marked({
      gfm: true,
      breaks: false,
      renderer,
      extensions: [
        {
          name: 'displayMath',
          level: 'block',
          start: (src: string) => src.indexOf('$$'),
          tokenizer: (src: string) => {
            const match = BLOCK_MATH.exec(src);
            if (!match) return undefined;
            return { type: 'displayMath', raw: match[0], text: match[1].trim() };
          },
          renderer: (token) => renderMath(token['text'], true),
        },
        {
          name: 'inlineMath',
          level: 'inline',
          start: (src: string) => src.indexOf('$'),
          tokenizer: (src: string) => {
            const match = INLINE_MATH.exec(src);
            if (!match) return undefined;
            return { type: 'inlineMath', raw: match[0], text: match[1] };
          },
          renderer: (token) => renderMath(token['text'], false),
        },
      ],
    });
  }

  /**
   * Renders a statement to HTML. Code spans and fenced blocks are lifted out
   * before parsing so a `$` inside a sample input is never read as math, then
   * put back verbatim. Raw HTML in the source is escaped: statements come from
   * the administrator, but there is no reason to trust a package file with
   * script execution.
   */
  render(markdown: string): string {
    const snippets: string[] = [];
    const withoutCode = markdown
      .replace(/```[\s\S]*?```/g, (block) => stash(snippets, blockHtml(block)))
      .replace(/`[^`\n]+`/g, (span) => stash(snippets, `<code>${escapeHtml(span.slice(1, -1))}</code>`))
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    const html = this.marked.parse(withoutCode, { async: false }) as string;

    return html.replace(/%%CJCODE(\d+)%%/g, (_match, index: string) => {
      return snippets[Number(index)] ?? '';
    });
  }
}

function stash(snippets: string[], html: string): string {
  snippets.push(html);
  return PLACEHOLDER(snippets.length - 1);
}

/** ```lang\ncode``` -> the HTML marked would have produced for it. */
function blockHtml(block: string): string {
  const body = block.replace(/^```[^\n]*\n?/, '').replace(/```$/, '');
  const language = /^```([^\n]*)/.exec(block)?.[1]?.trim();
  const attribute = language ? ` class="language-${escapeHtml(language)}"` : '';
  return `<pre><code${attribute}>${escapeHtml(body)}</code></pre>`;
}

function renderMath(source: string, displayMode: boolean): string {
  try {
    return katex.renderToString(source, {
      displayMode,
      throwOnError: false,
      strict: false,
      output: 'html',
    });
  } catch {
    // Never let a malformed formula blank out the whole statement.
    return `<code>${escapeHtml(source)}</code>`;
  }
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}