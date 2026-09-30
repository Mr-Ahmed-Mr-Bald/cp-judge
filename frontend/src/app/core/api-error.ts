import { HttpErrorResponse } from '@angular/common/http';

/**
 * A backend failure reduced to the three things the UI actually needs:
 * a sentence to show, the field it belongs to (if any), and the raw status.
 */
export interface ApiError {
  status: number;
  /** Sentence to render next to the form or inside the page-level alert. */
  message: string;
  /** Field name -> message, for 409 and 422 responses. */
  fieldErrors: Record<string, string>;
}

/** Pydantic wraps our own validators' text; unwrap it for display. */
function cleanMessage(raw: string): string {
  return raw
    .replace(/^Value error,\s*/, '')
    .replace(/^value is not a valid email address:?.*$/i, 'Enter a valid email address.')
    .replace(/^string should match pattern.*$/i, 'Enter a valid value.')
    .trim();
}

const FIELD_HINTS: ReadonlyArray<readonly [RegExp, string]> = [
  [/current password/i, 'current_password'],
  [/email/i, 'email'],
  [/handle/i, 'handle'],
  [/password/i, 'password'],
];

/**
 * The backend reports uniqueness as a free-text 409 detail
 * ("Email already registered") rather than as a field key, so the field is
 * recovered from the wording. Everything else falls back to no field.
 */
function fieldForDetail(detail: string): string | undefined {
  return FIELD_HINTS.find(([pattern]) => pattern.test(detail))?.[1];
}

export function toApiError(error: unknown): ApiError {
  if (!(error instanceof HttpErrorResponse)) {
    return {
      status: 0,
      message: 'Could not reach the server. Check that the API is running.',
      fieldErrors: {},
    };
  }

  const status = error.status;
  const body = error.error as unknown;

  if (status === 0) {
    return {
      status,
      message: 'Could not reach the server. Check that the API is running.',
      fieldErrors: {},
    };
  }

  const payload = (body ?? {}) as { detail?: unknown; message?: unknown };
  const detail = typeof payload.detail === 'string' ? payload.detail : '';

  // 422: FastAPI's validation envelope, one entry per rejected field.
  if (status === 422 && Array.isArray(payload.detail)) {
    const fieldErrors: Record<string, string> = {};
    for (const entry of payload.detail as Array<{ loc?: unknown[]; msg?: string }>) {
      const field = (entry.loc ?? []).filter((part) => part !== 'body').join('.');
      const message = cleanMessage(entry.msg ?? 'Invalid value.');
      if (!field) continue;
      // Keep the first complaint per field: it is the most specific one.
      fieldErrors[field] ??= message;
    }
    const first = Object.values(fieldErrors)[0];
    return { status, message: first ?? 'Please check the highlighted fields.', fieldErrors };
  }

  // Everything else uses a plain string detail.
  if (detail) {
    const field = fieldForDetail(detail);
    return {
      status,
      message: cleanMessage(detail),
      fieldErrors: field ? { [field]: cleanMessage(detail) } : {},
    };
  }

  return {
    status,
    message: status >= 500 ? 'The server ran into a problem.' : 'Request failed.',
    fieldErrors: {},
  };
}