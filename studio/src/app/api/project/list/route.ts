import { listProjects } from '@/lib/db/project-repo';
import { apiSuccess } from '@/lib/api/response';
import { requireAuth } from '@/lib/auth/session';
import { findOrCreateUser } from '@/lib/db/user-repo';
import { checkAccess } from '@/lib/db/rbac-repo';

export async function GET() {
  const [user, error] = await requireAuth();
  if (error) return error;
  const dbUser = findOrCreateUser(user.email, user.name);
  const projects = listProjects().filter(project => checkAccess(project.id, dbUser.id, 'viewer'));
  return apiSuccess({ projects });
}
