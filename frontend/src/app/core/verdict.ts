import { Verdict } from './models';

export interface VerdictInfo {
  label: string;
  /** Short explanation shown under the badge on the submission page. */
  hint: string;
  tone: 'ok' | 'bad' | 'warn' | 'neutral';
}

const VERDICTS: Record<Verdict, VerdictInfo> = {
  AC: { label: 'Accepted', hint: 'Every test passed.', tone: 'ok' },
  WA: { label: 'Wrong Answer', hint: 'The checker rejected the output.', tone: 'bad' },
  TL: { label: 'Time Limit Exceeded', hint: 'A test ran past the time limit.', tone: 'warn' },
  ML: { label: 'Memory Limit Exceeded', hint: 'A test was killed for using too much memory.', tone: 'warn' },
  RE: { label: 'Runtime Error', hint: 'A test crashed or exited with a nonzero code.', tone: 'bad' },
  CE: { label: 'Compile Error', hint: 'The source did not build with g++ -O2 -std=c++17.', tone: 'bad' },
  JE: { label: 'Judge Error', hint: 'The judge itself failed. This is not your fault.', tone: 'neutral' },
};

const UNKNOWN: VerdictInfo = { label: 'Unknown', hint: '', tone: 'neutral' };

export function verdictInfo(verdict: Verdict | null | undefined): VerdictInfo | null {
  if (!verdict) return null;
  return VERDICTS[verdict] ?? UNKNOWN;
}

/** Section 7.1: what the user sees while the submission is not DONE yet. */
export function statusLabel(
  status: string,
  currentTest: number | null,
): string {
  switch (status) {
    case 'PENDING':
      return 'Queued';
    case 'COMPILING':
      return 'Compiling';
    case 'RUNNING':
      return currentTest === null ? 'Running' : `Running test ${currentTest + 1}`;
    case 'DONE':
      return 'Done';
    default:
      return status;
  }
}