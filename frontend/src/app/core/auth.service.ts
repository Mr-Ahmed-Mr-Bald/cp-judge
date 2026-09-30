import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, switchMap, tap } from 'rxjs';
import { Role, TokenResponse, User } from './models';

const TOKEN_KEY = 'cpjudge.token';
const USER_KEY = 'cpjudge.user';

interface StoredUser {
  id: number;
  email: string;
  handle: string;
  role: Role;
  created_at: string;
}

/**
 * The session is a bearer token issued by POST /api/login plus the user object
 * from GET /api/me. The token is kept in localStorage so a reload keeps the
 * session; `expiresAt` is read straight out of the JWT so the UI can warn
 * before the 15 minute token lifetime runs out.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly _token = signal<string | null>(localStorage.getItem(TOKEN_KEY));
  private readonly _user = signal<StoredUser | null>(readStoredUser());
  private readonly _ready = signal(false);

  /** Resolves once the startup session check has finished. */
  readonly ready = this._ready.asReadonly();
  readonly user = this._user.asReadonly();
  readonly token = this._token.asReadonly();

  readonly isLoggedIn = computed(() => this._token() !== null && this._user() !== null);
  readonly handle = computed(() => this._user()?.handle ?? null);
  readonly isAdmin = computed(() => this._user()?.role === 'ADMIN');

  /** Epoch milliseconds at which the access token stops being accepted. */
  readonly expiresAt = computed(() => decodeExpiry(this._token()));

  readonly isExpiringSoon = computed(() => {
    const expiresAt = this.expiresAt();
    if (!expiresAt) return false;
    return expiresAt - Date.now() < 60_000;
  });

  /**
   * Called once while the app bootstraps. A stored token is only trusted
   * after GET /api/me confirms it is still valid, so an expired token from a
   * previous visit cannot leave the UI in a half-logged-in state.
   */
  restore(): Observable<unknown> {
    const token = this._token();
    if (!token) {
      this._ready.set(true);
      return new Observable<void>((subscriber) => {
        subscriber.next();
        subscriber.complete();
      });
    }

    return this.http.get<User>('/api/me').pipe(
      tap({
        next: (user) => this._adopt(token, user),
        error: () => this.clear(),
        complete: () => this._ready.set(true),
      }),
    );
  }

  /**
   * Resolves once the session is fully established: the token is stored and
   * GET /api/me has filled in the user. Callers can navigate straight after
   * without racing the second request, which would otherwise lose the session
   * on a fast reload.
   */
  login(email: string, password: string): Observable<User> {
    return this.http
      .post<TokenResponse>('/api/login', { email: email.trim(), password })
      .pipe(
        switchMap((response) => {
          localStorage.setItem(TOKEN_KEY, response.access_token);
          this._token.set(response.access_token);
          return this.http
            .get<User>('/api/me')
            .pipe(tap((user) => this._adopt(response.access_token, user)));
        }),
      );
  }

  /**
   * Registration returns the user but no token, so the new account signs in
   * immediately afterwards instead of sending the user to the login form.
   */
  register(email: string, handle: string, password: string): Observable<User> {
    return this.http
      .post<User>('/api/register', { email: email.trim(), handle: handle.trim(), password })
      .pipe(switchMap(() => this.login(email, password)));
  }

  /** Applies a user object returned by PATCH /api/me/handle. */
  updateUser(user: User): void {
    this._user.set(user);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  logout(): void {
    this.clear();
  }

  private _adopt(token: string, user: User): void {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    this._token.set(token);
    this._user.set(user);
  }

  private clear(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this._token.set(null);
    this._user.set(null);
    this._ready.set(true);
  }
}

function readStoredUser(): StoredUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

/** Reads `exp` out of a JWT payload without verifying it (the API does that). */
function decodeExpiry(token: string | null): number | null {
  if (!token) return null;
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}