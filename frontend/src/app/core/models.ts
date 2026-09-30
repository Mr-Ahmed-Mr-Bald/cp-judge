/**
 * Shapes returned by the backend. They mirror backend/schemas.py exactly;
 * keep this file in sync with any API change.
 */

export type Role = 'USER' | 'ADMIN';

export interface User {
  id: number;
  email: string;
  handle: string;
  role: Role;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ProblemListItem {
  id: number;
  slug: string;
  title: string;
  time_limit_ms: number;
  memory_limit_mb: number;
  tags: string[];
}

export interface ProblemDetail extends ProblemListItem {
  test_count: number;
  statement_md: string;
}

/** Section 7.1 of the spec. */
export type SubmissionStatus = 'PENDING' | 'COMPILING' | 'RUNNING' | 'DONE';

/** Section 6.1 of the spec, as implemented by the engine. */
export type Verdict = 'AC' | 'WA' | 'TL' | 'ML' | 'RE' | 'CE' | 'JE';

export interface SubmissionOut {
  id: number;
  problem_id: number;
  problem_slug: string;
  problem_title: string;
  status: SubmissionStatus;
  source_code: string;
  created_at: string;
  verdict: Verdict | null;
  current_test: number | null;
  failed_test: number | null;
  judged_at: string | null;
}

export interface SubmissionListItem {
  id: number;
  problem_id: number;
  problem_slug: string;
  problem_title: string;
  status: SubmissionStatus;
  created_at: string;
  verdict: Verdict | null;
  failed_test: number | null;
  judged_at: string | null;
}

/** The backend refuses sources larger than this (spec Section 4.2). */
export const SOURCE_MAX_BYTES = 64 * 1024;