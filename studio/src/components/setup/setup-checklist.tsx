'use client';

/**
 * SetupChecklist — fresh-install / standalone readiness panel (I-6.5).
 *
 * Renders the preflight checks (BYO key, secrets provider, Python bridge, Core
 * artifacts, auth) and an honest overall verdict: ready, or blocked with the
 * named blockers. Required-but-missing checks block; warnings do not.
 */

import type { SetupReadiness, CheckStatus } from '@/lib/setup/preflight';

const GLYPH: Record<CheckStatus, string> = { ok: '✓', warn: '!', missing: '✕' };

export function SetupChecklist({ readiness }: { readiness: SetupReadiness }) {
  return (
    <section data-testid="setup-checklist" className="setup-checklist">
      <header>
        <h2>Standalone-Setup (lokal-first, BYO-Key)</h2>
        <p
          data-testid="setup-verdict"
          data-ready={readiness.ready ? 'true' : 'false'}
          className={`setup-verdict ${readiness.ready ? 'is-ready' : 'is-blocked'}`}
        >
          {readiness.ready
            ? 'Bereit — alle Pflicht-Checks grün.'
            : `Nicht bereit: ${readiness.blockers.join(', ')}`}
        </p>
      </header>

      <ul className="setup-checks">
        {readiness.checks.map((c) => (
          <li
            key={c.key}
            data-testid={`setup-check-${c.key}`}
            data-status={c.status}
            className={`setup-check is-${c.status}`}
          >
            <span className="check-glyph" aria-hidden="true">
              {GLYPH[c.status]}
            </span>
            <span className="check-label">
              {c.label}
              {c.required ? '' : ' (optional)'}
            </span>
            <span className="check-detail">{c.detail}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
