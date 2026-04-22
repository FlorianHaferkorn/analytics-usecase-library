export function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return 'var(--accent)';
    case 'draft':
      return 'var(--warning)';
    case 'deprecated':
      return 'var(--danger)';
    default:
      return 'var(--ink-4)';
  }
}