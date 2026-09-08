/** Governance Review API — comments, snapshots, comparisons, and restore. */

import { handleReviewGET, handleReviewPOST } from './handlers';

export async function GET(request: Request) {
  return handleReviewGET(request);
}

export async function POST(request: Request) {
  return handleReviewPOST(request);
}
