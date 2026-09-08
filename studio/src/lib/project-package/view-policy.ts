export type SurfaceScope = 'library' | 'project' | 'administration';

/** Explicit data origin, independent from the project selector. No implicit fallback. */
export function surfaceScope(path: string, requested: 'library' | 'project'): SurfaceScope {
  if (/^\/(organizations|plugins|ai-config|ai-health)(\/|$)/.test(path)) return 'administration';
  if (/^\/(discover|discovery|package|architecture|engagement|automation)(\/|$)/.test(path)) return 'project';
  if (/^\/(library|catalog|templates|brand-lab|detail|brackets)(\/|$)/.test(path)) return 'library';
  return requested;
}

export function projectSurface(path: string): 'overview' | 'architecture' | 'decisions' | 'assurance' | 'unsupported' {
  if (path === '/overview') return 'overview';
  if (/^\/(blueprint|canvas|lineage|steering)(\/|$)/.test(path)) return 'architecture';
  if (path === '/approvals') return 'decisions';
  if (/^\/(health|drift)(\/|$)/.test(path)) return 'assurance';
  return 'unsupported';
}
