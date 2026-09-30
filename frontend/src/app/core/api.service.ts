import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  ProblemDetail,
  ProblemListItem,
  SubmissionListItem,
  SubmissionOut,
  User,
} from './models';

/**
 * Thin typed wrapper over the API described in spec Section 10. The base URL is
 * relative so the dev server proxy (proxy.conf.json) and a reverse proxy in
 * production both work without a rebuild.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  listProblems(): Observable<ProblemListItem[]> {
    return this.http.get<ProblemListItem[]>('/api/problems');
  }

  getProblem(slug: string): Observable<ProblemDetail> {
    return this.http.get<ProblemDetail>(`/api/problems/${encodeURIComponent(slug)}`);
  }

  submit(slug: string, sourceCode: string): Observable<SubmissionOut> {
    return this.http.post<SubmissionOut>(
      `/api/problems/${encodeURIComponent(slug)}/submissions`,
      { source_code: sourceCode },
    );
  }

  getSubmission(id: number): Observable<SubmissionOut> {
    return this.http.get<SubmissionOut>(`/api/submissions/${id}`);
  }

  /** `problemSlug` maps to the backend's `problem_slug` query parameter. */
  listSubmissions(problemSlug?: string, limit?: number): Observable<SubmissionListItem[]> {
    let params = new HttpParams();
    if (problemSlug) params = params.set('problem_slug', problemSlug);
    if (limit) params = params.set('limit', limit);
    return this.http.get<SubmissionListItem[]>('/api/submissions', { params });
  }

  changeHandle(handle: string): Observable<User> {
    return this.http.patch<User>('/api/me/handle', { handle });
  }

  changePassword(currentPassword: string, newPassword: string): Observable<User> {
    return this.http.patch<User>('/api/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }
}