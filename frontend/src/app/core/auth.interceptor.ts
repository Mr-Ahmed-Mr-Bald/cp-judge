import {
  HttpErrorResponse,
  HttpInterceptorFn,
  HttpRequest,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

/**
 * Endpoints where a 401 is the answer to the question, not a dead session.
 * PATCH /api/me/password answers 401 for a wrong current password, which must
 * not be mistaken for an expired token and throw the user out.
 */
const NO_SESSION_REDIRECT = ['/api/login', '/api/register', '/api/me/handle', '/api/me/password'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  const token = auth.token();
  const request: HttpRequest<unknown> = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(request).pipe(
    catchError((error: unknown) => {
      const expired = error instanceof HttpErrorResponse && error.status === 401;
      const isLoginAttempt = NO_SESSION_REDIRECT.some((path) => req.url.startsWith(path));

      if (expired && token && !isLoginAttempt) {
        auth.logout();
        void router.navigate(['/login'], { queryParams: { reason: 'expired' } });
      }

      return throwError(() => error);
    }),
  );
};