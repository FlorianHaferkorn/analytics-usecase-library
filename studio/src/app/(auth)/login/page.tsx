'use client';

import { signIn } from 'next-auth/react';
import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const searchParams = useSearchParams();
  // Avoid redirecting unauthenticated users into the Steering hub (which can chain
  // into additional redirects). Use Overview as the safe default.
  const callbackUrl = searchParams.get('callbackUrl') ?? '/overview';

  const handleDemoLogin = async () => {
    setIsLoading(true);
    await signIn('credentials', { email: email || 'demo@aurora-group.eu', callbackUrl });
  };

  const handleGitHub = async () => {
    setIsLoading(true);
    await signIn('github', { callbackUrl });
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--bg)',
      padding: 'var(--pad)',
    }}>
      <div style={{
        width: '100%',
        maxWidth: 400,
        backgroundColor: 'var(--panel)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--radius-xl)',
        padding: '40px',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '16px',
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg, var(--accent), var(--warning))',
            }} />
            <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ink)' }}>
              ActionReady Studio
            </span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--ink-3)' }}>
            Sign in to access your analytics workspace
          </p>
        </div>

        {/* GitHub */}
        <button
          onClick={handleGitHub}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '12px',
            backgroundColor: 'var(--bg-2)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--ink)',
            fontSize: '0.875rem',
            fontWeight: 600,
            cursor: isLoading ? 'wait' : 'pointer',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
          Continue with GitHub
        </button>

        {/* Divider */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '16px',
          marginBottom: '24px',
        }}>
          <div style={{ flex: 1, height: 1, backgroundColor: 'var(--line)' }} />
          <span style={{ fontSize: '0.75rem', color: 'var(--ink-4)' }}>or demo login</span>
          <div style={{ flex: 1, height: 1, backgroundColor: 'var(--line)' }} />
        </div>

        {/* Demo Credentials */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="demo@aurora-group.eu"
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: 'var(--bg-2)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--ink)',
              fontSize: '0.875rem',
            }}
          />
          <button
            onClick={handleDemoLogin}
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px',
              background: 'linear-gradient(135deg, var(--accent), oklch(0.65 0.15 165))',
              border: 'none',
              borderRadius: 'var(--radius-lg)',
              color: 'var(--bg)',
              fontSize: '0.875rem',
              fontWeight: 700,
              cursor: isLoading ? 'wait' : 'pointer',
            }}
          >
            {isLoading ? 'Signing in...' : 'Sign in with Demo'}
          </button>
        </div>

        <p style={{
          marginTop: '24px',
          fontSize: '0.6875rem',
          color: 'var(--ink-4)',
          textAlign: 'center',
        }}>
          Self-hosted &middot; Your data stays local &middot; BYOK for AI
        </p>
      </div>
    </div>
  );
}
