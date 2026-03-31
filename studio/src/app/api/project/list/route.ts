import { listProjects } from '@/lib/db/project-repo';
import { apiSuccess } from '@/lib/api/response';

export async function GET() {
  const projects = listProjects();
  return apiSuccess({ projects });
}
