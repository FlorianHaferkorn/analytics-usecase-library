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

/** A single org membership entry embedded in the JWT (ADR-0014 Festlegung 5). */
export interface OrgMembership {
  orgId: string;
  role: string;
}

const isProduction = process.env.NODE_ENV === 'production';
const hasGitHubOAuth = Boolean(process.env.GITHUB_ID && process.env.GITHUB_SECRET);

// ── AuthN provider policy (ADR-0016 Option A · T1-Compliance · T5=C) ─────────────
// DEFAULT-PFAD HAT KEINEN EXTERNEN SOCIAL-IdP: GitHub wird NUR verdrahtet, wenn
// GITHUB_ID+GITHUB_SECRET gesetzt sind (opt-in) → erfüllt die T1-Auflage „kein
// Social-IdP im Default". Wird GitHub in Produktion aktiviert, MUSS es ein
// organisatorisch freigegebener IdP sein (Login-Daten verlassen die EU-self-hosted-
// Grenze — siehe compliance/auth_stack_data_residency.md §3).
// Der Credentials-"Demo Login" ist DEV-ONLY (in Produktion aus).
// OFFEN (T5-Ziel A, aufgeschoben): Produktion hat noch KEINE eingebaute
// compliance-konforme Login-Methode — die passwortlose Magic-Link-Variante (EU-
// E-Mail-Provider) ist der geplante Default. Bis dahin muss ein Prod-Deploy einen
// freigegebenen IdP konfigurieren, sonst ist `providers` in Prod leer (kein Login).
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
          try {
            const { lookupOrgMemberships } = await import(
              /* webpackIgnore: true */ './org-membership-lookup'
            );
            token.org_memberships = await lookupOrgMemberships(email);
          } catch {
            token.org_memberships = [];
          }
        } else {
          token.project_memberships = [];
          token.org_memberships = [];
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
      if (token.org_memberships) {
        (session as unknown as Record<string, unknown>).org_memberships =
          token.org_memberships;
      }
      return session;
    },
  },
});
