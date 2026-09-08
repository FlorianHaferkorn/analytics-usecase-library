'use client';

import { AiField } from '@/components/ai/ai-field';

interface Props {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
  entityType: 'kpi' | 'bracket' | 'action_code' | 'use_case';
  entityId: string;
  entityName: string;
  fieldName: string;
}

export function EditableList({
  label,
  items,
  onChange,
  placeholder,
  entityType,
  entityId,
  entityName,
  fieldName,
}: Props) {
  function updateItem(index: number, newVal: string) {
    const next = [...items];
    next[index] = newVal;
    onChange(next);
  }

  function removeItem(index: number) {
    onChange(items.filter((_, i) => i !== index));
  }

  function addItem() {
    onChange([...items, '']);
  }

  return (
    <div>
      <div
        style={{
          fontSize: 'var(--text-xs)',
          textTransform: 'uppercase',
          color: 'var(--ink-3)',
          letterSpacing: '0.06em',
          marginBottom: 10,
          fontWeight: 500,
        }}
      >
        {label}
      </div>

      {items.map((item, index) => (
        <div
          key={index}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 8,
          }}
        >
          <div style={{ flex: 1 }}>
            <AiField
              entityType={entityType}
              entityId={entityId}
              entityName={entityName}
              fieldName={`${fieldName}[${index}]`}
              fieldLabel={label}
              value={item}
              onChange={(newVal) => updateItem(index, newVal)}
              placeholder={placeholder}
            />
          </div>
          <button
            onClick={() => removeItem(index)}
            title="Remove"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--ink-4)',
              cursor: 'pointer',
              fontSize: 16,
              padding: '0 4px',
              flexShrink: 0,
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>
      ))}

      <button
        onClick={addItem}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 4,
          background: 'transparent',
          border: '1px solid var(--line)',
          borderRadius: 6,
          color: 'var(--ink-3)',
          fontSize: 12,
          padding: '4px 10px',
          cursor: 'pointer',
          marginTop: 4,
        }}
      >
        + Add item
      </button>
    </div>
  );
}
