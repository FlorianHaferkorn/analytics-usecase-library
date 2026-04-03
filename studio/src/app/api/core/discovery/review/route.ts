import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { apiError, apiSuccess } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

interface ReviewElementInput {
  type: 'anchor' | 'kpi' | 'action';
  id: string;
  name: string;
  source?: string;
}

interface ReviewMatch {
  id: string;
  name: string;
  reason: 'exact-id' | 'exact-name' | 'similar-name';
}

function isReviewElement(value: unknown): value is ReviewElementInput {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Record<string, unknown>;
  return (
    (candidate.type === 'anchor' || candidate.type === 'kpi' || candidate.type === 'action') &&
    typeof candidate.id === 'string' &&
    candidate.id.length > 0 &&
    typeof candidate.name === 'string' &&
    candidate.name.length > 0
  );
}

function normalize(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return apiError(ErrorCode.VALIDATION_ERROR, 'Invalid JSON body', 400);
  }

  const rawElements = (body as { elements?: unknown })?.elements;
  if (!Array.isArray(rawElements)) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'elements must be an array', 400);
  }

  const elements = rawElements.filter(isReviewElement);
  if (elements.length === 0) {
    return apiError(ErrorCode.VALIDATION_ERROR, 'No valid elements to review', 400);
  }

  const [kpis, actions] = await Promise.all([loadKpiCatalog(), loadAllActionCodes()]);

  const results = elements.map((element) => {
    if (element.type === 'anchor') {
      return {
        ...element,
        status: 'informational',
        recommendation: 'capture',
        matches: [] as ReviewMatch[],
        message: 'Strategy anchors are draft-only until linked to a use case or spine.',
      };
    }

    const normalizedName = normalize(element.name);
    const catalog = element.type === 'kpi'
      ? kpis.map((kpi) => ({ id: kpi.kpi_id, name: kpi.kpi_key ?? kpi.kpi_id }))
      : actions.map((action) => ({ id: action.id, name: action.name }));

    const matches: ReviewMatch[] = [];
    for (const item of catalog) {
      if (item.id.toLowerCase() === element.id.toLowerCase()) {
        matches.push({ id: item.id, name: item.name, reason: 'exact-id' });
      } else if (normalize(item.name) === normalizedName) {
        matches.push({ id: item.id, name: item.name, reason: 'exact-name' });
      } else if (normalizedName.length >= 6 && (normalize(item.name).includes(normalizedName) || normalizedName.includes(normalize(item.name)))) {
        matches.push({ id: item.id, name: item.name, reason: 'similar-name' });
      }
    }

    const dedupedMatches = matches.filter(
      (match, index) => matches.findIndex((candidate) => candidate.id === match.id && candidate.reason === match.reason) === index,
    ).slice(0, 4);

    const hasExactId = dedupedMatches.some((match) => match.reason === 'exact-id');
    const hasExactName = dedupedMatches.some((match) => match.reason === 'exact-name');
    const hasSimilar = dedupedMatches.some((match) => match.reason === 'similar-name');

    let status: 'new' | 'warning' | 'conflict' = 'new';
    let recommendation: 'create' | 'reuse' | 'review' = 'create';
    let message = 'No matching governed asset found.';

    if (hasExactId) {
      status = 'conflict';
      recommendation = 'reuse';
      message = 'Exact ID already exists in the governed registry.';
    } else if (hasExactName) {
      status = 'warning';
      recommendation = 'review';
      message = 'A governed asset already exists with the same name.';
    } else if (hasSimilar) {
      status = 'warning';
      recommendation = 'review';
      message = 'Potentially similar governed assets exist. Compare before drafting.';
    }

    return {
      ...element,
      status,
      recommendation,
      matches: dedupedMatches,
      message,
    };
  });

  const summary = {
    total: results.length,
    newCount: results.filter((item) => item.status === 'new').length,
    warningCount: results.filter((item) => item.status === 'warning').length,
    conflictCount: results.filter((item) => item.status === 'conflict').length,
    informationalCount: results.filter((item) => item.status === 'informational').length,
  };

  return apiSuccess({ summary, results });
}