export function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return 'var(--mint)';
    case 'draft':
      return 'var(--gold)';
    case 'deprecated':
      return 'var(--danger)';
    default:
      return 'var(--ink-4)';
  }
}