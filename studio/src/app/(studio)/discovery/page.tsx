export default function DiscoveryPage() {
  return (
    <div style={{ display: 'flex', gap: 'var(--sp-2)', height: 'calc(100vh - 56px - var(--sp-6))' }}>
      {/* Source Panel (left) */}
      <div
        style={{
          width: '300px',
          flexShrink: 0,
          backgroundColor: 'var(--slate-800)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--slate-700)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={{ padding: 'var(--sp-2)', borderBottom: '1px solid var(--slate-700)' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: 'var(--sp-1)' }}>
            Sources
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--slate-500)' }}>
            Upload PDFs, add URLs, or paste text to extract strategy anchors.
          </p>
        </div>

        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--sp-3)',
          }}
        >
          <div
            style={{
              padding: 'var(--sp-3)',
              border: '2px dashed var(--slate-600)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center',
              width: '100%',
            }}
          >
            <p style={{ fontSize: '1.5rem', marginBottom: 'var(--sp-1)' }}>+</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>
              Drop files here or click to upload
            </p>
            <p style={{ fontSize: '0.6875rem', color: 'var(--slate-600)', marginTop: '4px' }}>
              PDF, DOCX, or URL
            </p>
          </div>
        </div>

        <div style={{ padding: 'var(--sp-1-5)', borderTop: '1px solid var(--slate-700)' }}>
          <p style={{ fontSize: '0.6875rem', color: 'var(--slate-600)', textAlign: 'center' }}>
            BYOK: Connect your AI provider in Settings
          </p>
        </div>
      </div>

      {/* Chat Panel (center) */}
      <div
        style={{
          flex: 1,
          backgroundColor: 'var(--slate-800)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--slate-700)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={{ padding: 'var(--sp-2)', borderBottom: '1px solid var(--slate-700)' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
            Discovery Chat
          </h3>
        </div>

        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--sp-3)',
          }}
        >
          <div style={{ textAlign: 'center', maxWidth: '400px' }}>
            <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--slate-200)', marginBottom: 'var(--sp-1)' }}>
              Start a Discovery Session
            </p>
            <p style={{ fontSize: '0.875rem', color: 'var(--slate-400)', lineHeight: 1.6 }}>
              Upload a business report or annual report, then ask the AI to extract
              strategy anchors, identify strategic KPIs, and suggest the Golden Thread structure.
            </p>
          </div>
        </div>

        <div style={{ padding: 'var(--sp-1-5)', borderTop: '1px solid var(--slate-700)' }}>
          <div
            style={{
              display: 'flex',
              gap: 'var(--sp-1)',
            }}
          >
            <input
              type="text"
              placeholder="Ask about strategy, KPIs, or actions..."
              disabled
              style={{
                flex: 1,
                padding: 'var(--sp-1) var(--sp-1-5)',
                backgroundColor: 'var(--slate-900)',
                border: '1px solid var(--slate-700)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--slate-400)',
                fontSize: '0.875rem',
              }}
            />
            <button
              disabled
              style={{
                padding: 'var(--sp-1) var(--sp-2)',
                backgroundColor: 'var(--mint-dark, #00A888)',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                color: 'var(--slate-950)',
                fontWeight: 600,
                fontSize: '0.875rem',
                opacity: 0.5,
                cursor: 'not-allowed',
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>

      {/* Result Panel (right) */}
      <div
        style={{
          width: '300px',
          flexShrink: 0,
          backgroundColor: 'var(--slate-800)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--slate-700)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={{ padding: 'var(--sp-2)', borderBottom: '1px solid var(--slate-700)' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
            Extracted Elements
          </h3>
        </div>
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--sp-3)',
          }}
        >
          <p style={{ fontSize: '0.75rem', color: 'var(--slate-500)', textAlign: 'center' }}>
            Strategy anchors, KPIs, and action codes will appear here after discovery.
          </p>
        </div>
      </div>
    </div>
  );
}
