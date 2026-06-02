'use client';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
  height?: string;
}

export function MarkdownEditor({
  value,
  onChange,
  readOnly = false,
  height = '480px',
}: MarkdownEditorProps) {
  return (
    <textarea
      value={value}
      readOnly={readOnly}
      onChange={(e) => onChange(e.target.value)}
      spellCheck={false}
      className="w-full font-mono text-[13px] text-foreground bg-background-muted border-0 outline-none resize-y p-4 leading-relaxed"
      style={{ minHeight: height }}
      aria-label="Factsheet markdown editor"
    />
  );
}
