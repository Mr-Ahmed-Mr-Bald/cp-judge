import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { toApiError } from '../../core/api-error';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  imports: [FormsModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './login.html',
})
export class LoginPage {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected email = '';
  protected password = '';

  protected readonly submitting = signal(false);
  protected readonly error = signal<string | null>(null);

  /** Set when the interceptor bounced the user here after the token expired. */
  protected readonly notice = signal<string | null>(
    this.route.snapshot.queryParamMap.get('reason') === 'expired'
      ? 'Your session expired. Please log in again.'
      : null,
  );

  protected async submit(): Promise<void> {
    this.error.set(null);
    this.notice.set(null);

    if (!this.email || !this.password) {
      this.error.set('Enter your email and password.');
      return;
    }

    this.submitting.set(true);
    try {
      await firstValueFrom(this.auth.login(this.email.trim(), this.password));

      // Guard redirects record where the visitor was headed; only same-site
      // paths are honoured so the query string cannot be abused as a redirect.
      const next = this.route.snapshot.queryParamMap.get('next');
      await this.router.navigateByUrl(next?.startsWith('/') ? next : '/problems');
    } catch (failure) {
      const apiError = toApiError(failure);
      // The API answers a bad login with one generic message so it cannot be
      // used to discover which emails exist; never say which field was wrong.
      this.error.set(
        apiError.status === 401 || apiError.status === 422
          ? 'That email and password combination did not work.'
          : apiError.message,
      );
      this.password = '';
    } finally {
      this.submitting.set(false);
    }
  }
}