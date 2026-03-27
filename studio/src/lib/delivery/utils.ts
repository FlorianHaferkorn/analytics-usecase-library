/** Sanitize a string for use as an identifier (lowercase, alphanumeric + underscores). */
export function sanitize(s: string): string {
  return s.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
}
