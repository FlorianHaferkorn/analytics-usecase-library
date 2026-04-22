'use client';

import { useCallback, useState, useRef } from 'react';
import dynamic from 'next/dynamic';
import { parseYaml } from '@/lib/core/yaml-loader';
import { validate, type ValidationResult } from '@/lib/validation/schema-validator';

const MonacoEditor = dynamic(() => import('@monaco-editor/react').then(m => m.default), {
  ssr: false,
  loading: () => (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      color: 'var(--ink-4)',
      fontSize: '0.875rem',
    }}>
      Loading editor...
    </div>
  ),
});

interface Props {
  initialValue: string;
  schema?: Record<string, unknown>;
  onChange?: (value: string, parsed: unknown) => void;
  readOnly?: boolean;
  height?: string;
}

const DEBOUNCE_MS = 300;

export function YamlEditor({
  initialValue,
  schema,
  onChange,
  readOnly = false,
  height = '500px',
}: Props) {
  const [validation, setValidation] = useState<ValidationResult>({ valid: true, errors: [] });
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null);

  const handleChange = useCallback(
    (value: string | undefined) => {
      if (!value) return;

      if (timerRef.current) clearTimeout(timerRef.current);

      timerRef.current = setTimeout(() => {
        try {
          const parsed = parseYaml<unknown>(value);

          if (schema) {
            const result = validate(schema, parsed);
            setValidation(result);
          } else {
            setValidation({ valid: true, errors: [] });
          }

          onChange?.(value, parsed);
        } catch {
          setValidation({
            valid: false,
            errors: [{ path: '/', message: 'Invalid YAML syntax', keyword: 'syntax' }],
          });
        }
      }, DEBOUNCE_MS);
    },
    [schema, onChange]
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '4px 8px',
          backgroundColor: 'var(--bg)',
          borderBottom: '1px solid var(--line)',
          fontSize: '0.6875rem',
        }}
      >
        <span style={{ color: 'var(--ink-4)' }}>YAML</span>
        <span
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            color: validation.valid ? 'var(--mint)' : 'var(--danger)',
          }}
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: validation.valid ? 'var(--mint)' : 'var(--danger)',
            }}
          />
          {validation.valid
            ? 'Valid'
            : `${validation.errors.length} error${validation.errors.length > 1 ? 's' : ''}`}
        </span>
      </div>

      <div style={{ flex: 1 }}>
        <MonacoEditor
          defaultLanguage="yaml"
          defaultValue={initialValue}
          onChange={handleChange}
          theme="vs-dark"
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: 'var(--font-mono)',
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            tabSize: 2,
            padding: { top: 8 },
          }}
        />
      </div>

      {!validation.valid && (
        <div
          style={{
            maxHeight: '120px',
            overflow: 'auto',
            padding: '8px',
            backgroundColor: 'var(--bg)',
            borderTop: '1px solid var(--line)',
          }}
        >
          {validation.errors.map((err, i) => (
            <div
              key={i}
              style={{
                fontSize: '0.75rem',
                color: 'var(--danger)',
                padding: '2px 0',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <span style={{ color: 'var(--ink-4)' }}>{err.path}</span> {err.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
