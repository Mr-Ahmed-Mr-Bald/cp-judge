import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { toApiError } from '../../core/api-error';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './register.html',
})
export class RegisterPage {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected email = '';
  protected handle = '';
  protected password = '';
  protected confirmPassword = '';

  protected readonly submitting = signal(false);
  protected readonly error = signal<string | null>(null);
  /** Field name -> message, filled from 409 (taken) and 422 (invalid). */
  protected readonly fieldErrors = signal<Record<string, string>>({});

  protected fieldError(field: string): string | null {
    return this.fieldErrors()[field] ?? null;
  }

  protected async submit(): Promise<void> {
    this.error.set(null);
    this.fieldErrors.set({});

    if (this.password !== this.confirmPassword) {
      this.fieldErrors.set({ confirmPassword: 'The two passwords do not match.' });
      return;
    }

    this.submitting.set(true);
    try {
      await firstValueFrom(this.auth.register(this.email.trim(), this.handle.trim(), this.password));

      const next = this.route.snapshot.queryParamMap.get('next');
      await this.router.navigateByUrl(next?.startsWith('/') ? next : '/problems');
    } catch (failure) {
      const apiError = toApiError(failure);
      this.fieldErrors.set(apiError.fieldErrors);
      this.error.set(
        Object.keys(apiError.fieldErrors).length > 0 ? null : apiError.message,
      );
    } finally {
      this.submitting.set(false);
    }
  }
}