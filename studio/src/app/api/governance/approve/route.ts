/** Governance Approval API — bracket lifecycle transitions. */

import { handleApproveGET, handleApprovePOST } from './handlers';

export async function GET(request: Request) {
  return handleApproveGET(request);
}

export async function POST(request: Request) {
  return handleApprovePOST(request);
}
