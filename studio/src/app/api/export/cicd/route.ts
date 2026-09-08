import { apiError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function POST() {
  return apiError(
    ErrorCode.UNSUPPORTED,
    'Generated CI/CD is not a governed delivery target. Package validated artifacts first, then use the customer-approved platform deployment pipeline and official vendor CLI.',
    410,
  );
}
