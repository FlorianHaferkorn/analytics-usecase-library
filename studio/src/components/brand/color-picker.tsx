'use client';

import styles from './color-picker.module.css';

interface Props {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export function ColorPicker({ label, value, onChange }: Props) {
  return (
    <div className={styles.picker}>
      <input
        type="color"
        aria-label={`${label} color`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={styles.swatch}
      />
      <div className={styles.copy}>
        <p className={styles.label}>{label}</p>
        <p className={styles.value}>{value}</p>
      </div>
    </div>
  );
}
