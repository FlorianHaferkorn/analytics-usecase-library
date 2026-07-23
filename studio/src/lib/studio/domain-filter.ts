/** Client-side domain filter — sidebar, brackets, KPI tags, contracts. */

/** Root segment before optional " / …" sub-domain. */
export function domainRoot(domain: string): string {
  return domain.split('/')[0]?.trim() ?? domain.trim();
}

/** Stable slug for cross-vocabulary matching (brackets, KPI tags, contracts). */
export function domainSlug(value: string): string {
  return domainRoot(value)
    .toLowerCase()
    .replace(/\s*&\s*/g, '-and-')
    .replace(/[_\s]+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

/** Known alias groups — first entry is the canonical slug. */
const DOMAIN_ALIAS_GROUPS: readonly string[][] = [
  ['commercial', 'commercial-sales', 'customer-and-market', 'sales', 'growth'],
  ['finance', 'financial', 'risk'],
  ['operations', 'ops', 'efficiency', 'quality'],
  ['supply-chain', 'scm', 'planning'],
  ['experience', 'service', 'customer'],
  ['people', 'people-and-culture', 'people-culture', 'hr', 'human-resources'],
  ['executive', 'executive-cross-functional', 'cross-functional', 'governance'],
  ['esg', 'sustainability'],
];

const CANONICAL_DOMAIN = new Map<string, string>(
  DOMAIN_ALIAS_GROUPS.flatMap(([canonical, ...aliases]) =>
    [canonical, ...aliases].map((alias) => [alias, canonical] as const),
  ),
);

export function canonicalDomain(value: string): string {
  const slug = domainSlug(value);
  return CANONICAL_DOMAIN.get(slug) ?? slug;
}

export function matchesDomainFilter(
  itemDomain: string | undefined | null,
  filter: string | null | undefined,
): boolean {
  if (!filter) return true;
  if (!itemDomain) return false;

  const filterCanonical = canonicalDomain(filter);
  const itemCanonical = canonicalDomain(itemDomain);
  if (filterCanonical === itemCanonical) return true;

  const f = filter.trim().toLowerCase();
  const d = itemDomain.trim().toLowerCase();
  const root = domainRoot(itemDomain).toLowerCase();

  return (
    root === f ||
    d === f ||
    d.startsWith(`${f} /`) ||
    d.startsWith(`${f}/`) ||
    root.startsWith(`${f} `)
  );
}

export function matchesDomainTags(
  tags: string[] | undefined,
  filter: string | null | undefined,
): boolean {
  if (!filter) return true;
  if (!tags?.length) return false;
  return tags.some((tag) => matchesDomainFilter(tag, filter));
}

export function filterByDomain<T>(
  items: T[],
  filter: string | null | undefined,
  getDomain: (item: T) => string | undefined | null,
): T[] {
  if (!filter) return items;
  return items.filter((item) => matchesDomainFilter(getDomain(item), filter));
}
