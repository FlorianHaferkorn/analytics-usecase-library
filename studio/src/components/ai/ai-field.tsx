'use client';

import { useState, type CSSProperties } from 'react';
import { useAiField, type FieldContext } from '@/hooks/use-ai-field';
import { AiAssistButton } from './ai-assist-button';
import { AiAssistDrawer } from './ai-assist-drawer';

interface Props {
  entityType: 'kpi' | 'bracket' | 'action_code' | 'use_case';
  entityId: string;
  entityName: string;
  fieldName: string;
  fieldLabel: string;
  value: string;
  onChange: (value: string) => void;
  multiline?: boolean;
  rows?: number;
  placeholder?: string;
  relatedKpiIds?: string[];
  domainContext?: string;
  style?: CSSProperties;
}

const BASE_FIELD_STYLE: CSSProperties = {
  width: '100%',
  background: 'var(--bg-2)',
  border: '1px solid var(--line)',
  borderRadius: 6,
  padding: '8px 36px 8px 12px',
  color: 'var(--ink)',
  fontSize: 13,
  fontFamily: 'inherit',
  lineHeight: 1.5,
  outline: 'none',
  boxSizing: 'border-box',
};

interface InputFieldProps {
  value: string;
  placeholder?: string;
  extraStyle?: CSSProperties;
  onChange: (value: string) => void;
}

function InputField({ value, placeholder, extraStyle, onChange }: InputFieldProps) {
  const [focused, setFocused] = useState(false);

  return (
    <input
      type="text"
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={{
        ...BASE_FIELD_STYLE,
        borderColor: focused ? 'var(--accent)' : 'var(--line)',
        ...extraStyle,
      }}
    />
  );
}

interface TextareaFieldProps {
  value: string;
  placeholder?: string;
  rows?: number;
  extraStyle?: CSSProperties;
  onChange: (value: string) => void;
}

function TextareaField({ value, placeholder, rows = 3, extraStyle, onChange }: TextareaFieldProps) {
  const [focused, setFocused] = useState(false);

  return (
    <textarea
      value={value}
      placeholder={placeholder}
      rows={rows}
      onChange={(e) => onChange(e.target.value)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={{
        ...BASE_FIELD_STYLE,
        borderColor: focused ? 'var(--accent)' : 'var(--line)',
        resize: 'vertical',
        ...extraStyle,
      }}
    />
  );
}

export function AiField({
  entityType,
  entityId,
  entityName,
  fieldName,
  fieldLabel,
  value,
  onChange,
  multiline = false,
  rows = 3,
  placeholder,
  relatedKpiIds,
  domainContext,
  style,
}: Props) {
  const { isOpen, isLoading, suggestions, rawStream, close, fetchSuggestions } = useAiField();

  const handleAssistClick = () => {
    const ctx: FieldContext = {
      entityType,
      entityId,
      entityName,
      fieldName,
      fieldLabel,
      currentValue: value,
      relatedKpiIds,
      domainContext,
    };
    fetchSuggestions(ctx);
  };

  const handleSelect = (text: string) => {
    onChange(text);
  };

  return (
    <div>
      <div style={{ position: 'relative' }}>
        {multiline ? (
          <TextareaField
            value={value}
            placeholder={placeholder}
            rows={rows}
            extraStyle={style}
            onChange={onChange}
          />
        ) : (
          <InputField
            value={value}
            placeholder={placeholder}
            extraStyle={style}
            onChange={onChange}
          />
        )}
        <AiAssistButton onClick={handleAssistClick} isActive={isOpen} />
      </div>

      <AiAssistDrawer
        isOpen={isOpen}
        isLoading={isLoading}
        suggestions={suggestions}
        rawStream={rawStream}
        onSelect={handleSelect}
        onClose={close}
      />
    </div>
  );
}
