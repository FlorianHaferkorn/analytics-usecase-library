import NextAuth from 'next-auth';
import GitHub from 'next-auth/providers/github';
import Credentials from 'next-auth/providers/credentials';
import { validateAuthEnv } from './env-check';

validateAuthEnv();

const isProduction = process.env.NODE_ENV === 'production';

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    GitHub({
      clientId: process.env.GITHUB_ID ?? '',
      clientSecret: process.env.GITHUB_SECRET ?? '',
    }),
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
  ],
  pages: {
    signIn: '/login',
  },
  session: { strategy: 'jwt' },
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    session({ session, token }) {
      if (session.user && token.id) {
        (session.user as unknown as Record<string, unknown>).id = token.id as string;
      }
      return session;
    },
  },
});
