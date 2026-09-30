import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { toApiError } from '../../core/api-error';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-settings',
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './settings.html',
  styles: `
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.5rem;
      align-items: start;
    }

    .card h2 {
      font-size: 1.05rem;
      margin: 0 0 0.25rem;
    }

    .account {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      padding-bottom: 0.9rem;
      margin-bottom: 0.35rem;
      border-bottom: 1px solid var(--border);
      font-size: 0.88rem;
    }

    .note {
      border-left: 3px solid var(--warn);
    }
  `,
})
export class SettingsPage {
  private readonly api = inject(ApiService);
  protected readonly auth = inject(AuthService);

  protected handle = this.auth.handle() ?? '';
  protected currentPassword = '';
  protected newPassword = '';
  protected confirmPassword = '';

  protected readonly savingHandle = signal(false);
  protected readonly savingPassword = signal(false);
  protected readonly handleError = signal<string | null>(null);
  protected readonly handleFieldErrors = signal<Record<string, string>>({});
  protected readonly handleDone = signal(false);

  protected readonly passwordError = signal<string | null>(null);
  protected readonly passwordFieldErrors = signal<Record<string, string>>({});
  protected readonly passwordDone = signal(false);

  /** The seeded administrator is immutable (spec Section 4.3). */
  protected readonly isAdmin = this.auth.isAdmin;

  protected handleFieldError(): string | null {
    return this.handleFieldErrors()['handle'] ?? null;
  }

  protected currentPasswordError(): string | null {
    return this.passwordFieldErrors()['current_password'] ?? null;
  }

  protected newPasswordError(): string | null {
    return this.passwordFieldErrors()['new_password'] ?? null;
  }

  protected async saveHandle(): Promise<void> {
    this.handleError.set(null);
    this.handleDone.set(false);
    this.handleFieldErrors.set({});

    if (this.handle.trim().length < 3) {
      this.handleFieldErrors.set({ handle: 'Handles need at least 3 characters.' });
      return;
    }

    this.savingHandle.set(true);
    try {
      // A 409 here means the handle was taken between the form being shown and
      // the save: the database constraint decides, not a pre-check.
      const user = await firstValueFrom(this.api.changeHandle(this.handle.trim()));
      this.auth.updateUser(user);
      this.handleDone.set(true);
    } catch (failure) {
      const apiError = toApiError(failure);
      this.handleFieldErrors.set(apiError.fieldErrors);
      this.handleError.set(Object.keys(apiError.fieldErrors).length ? null : apiError.message);
    } finally {
      this.savingHandle.set(false);
    }
  }

  protected async savePassword(): Promise<void> {
    this.passwordError.set(null);
    this.passwordDone.set(false);
    this.passwordFieldErrors.set({});

    if (this.newPassword !== this.confirmPassword) {
      this.passwordFieldErrors.set({ new_password: 'The two passwords do not match.' });
      return;
    }

    this.savingPassword.set(true);
    try {
      const user = await firstValueFrom(
        this.api.changePassword(this.currentPassword, this.newPassword),
      );
      // The response carries the current user; keep the header in sync.
      this.auth.updateUser(user);
      this.currentPassword = '';
      this.newPassword = '';
      this.confirmPassword = '';
      this.passwordDone.set(true);
    } catch (failure) {
      const apiError = toApiError(failure);
      this.passwordFieldErrors.set(apiError.fieldErrors);
      this.passwordError.set(Object.keys(apiError.fieldErrors).length ? null : apiError.message);
    } finally {
      this.savingPassword.set(false);
    }
  }
}