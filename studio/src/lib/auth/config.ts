import NextAuth from 'next-auth';
import GitHub from 'next-auth/providers/github';
import Credentials from 'next-auth/providers/credentials';
import { validateAuthEnv } from './env-check';

validateAuthEnv();

/** A single project membership entry embedded in the JWT. */
export interface ProjectMembership {
  projectId: string;
  role: string;
}

const isProduction = process.env.NODE_ENV === 'production';
const hasGitHubOAuth = Boolean(process.env.GITHUB_ID && process.env.GITHUB_SECRET);

const providers = [
  ...(hasGitHubOAuth
    ? [
        GitHub({
          clientId: process.env.GITHUB_ID ?? '',
          clientSecret: process.env.GITHUB_SECRET ?? '',
        }),
      ]
    : []),
  // Credentials provider is disabled in production for security.
  ...(!isProduction
    ? [
        Credentials({
          name: 'Demo Login',
          credentials: {
            email: { label: 'Email', type: 'email', placeholder: 'demo@aurora-group.eu' },
          },
          async authorize(credentials) {
            const email = credentials?.email as string | undefined;
            if (!email) return null;
            return { id: email, name: email.split('@')[0], email };
          },
        }),
      ]
    : []),
];

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers,
  pages: {
    signIn: '/login',
  },
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        // Populate project_memberships at sign-in time.
        // The membership-lookup module uses better-sqlite3 (Node.js only).
        // Dynamic import keeps the sqlite dependency out of the Edge bundle.
        const email = user.email ?? (token.email as string | undefined);
        if (email) {
          try {
            const { lookupProjectMemberships } = await import(
              /* webpackIgnore: true */ './membership-lookup'
            );
            token.project_memberships = await lookupProjectMemberships(email);
          } catch {
            token.project_memberships = [];
          }
        } else {
          token.project_memberships = [];
        }
      }
      return token;
    },
    session({ session, token }) {
      if (session.user && token.id) {
        (session.user as unknown as Record<string, unknown>).id = token.id as string;
      }
      if (token.project_memberships) {
        (session as unknown as Record<string, unknown>).project_memberships =
          token.project_memberships;
      }
      return session;
    },
  },
});
