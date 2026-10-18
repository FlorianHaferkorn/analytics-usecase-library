/**
 * Read an API error body on the client.
 *
 * Studio routes answer { error: { code, message } } (lib/api/response.ts). Older
 * responses and test fixtures may still carry { error: '<text>' }; both are read here
 * so a component never shows "[object Object]".
 */

type ErrorBody = { error?: unknown } | null | undefined;

export function apiErrorMessage(body: unknown, fallback: string): string {
  const error = (body as ErrorBody)?.error;
  if (typeof error === 'string' && error) return error;
  if (error && typeof error === 'object') {
    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string' && message) return message;
  }
  return fallback;
}

export function apiErrorCode(body: unknown): string | undefined {
  const error = (body as ErrorBody)?.error;
  const code = error && typeof error === 'object' ? (error as { code?: unknown }).code : undefined;
  return typeof code === 'string' ? code : undefined;
}
