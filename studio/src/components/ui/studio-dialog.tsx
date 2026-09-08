'use client';

import { useEffect, useId, useRef, type ReactNode } from 'react';
import styles from './studio-dialog.module.css';

/** Native modal traps focus, makes the background inert and restores the trigger. */
export function StudioDialog({ open, title, description, onClose, children }: {
  open: boolean; title: string; description?: string; onClose: () => void; children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog || !open) return;
    const trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialog.showModal();
    dialog.querySelector<HTMLElement>('[data-autofocus]')?.focus();
    return () => { dialog.close(); if (trigger?.isConnected) trigger.focus(); };
  }, [open]);
  return (
    <dialog ref={ref} className={styles.dialog} aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      onCancel={(event) => { event.preventDefault(); onClose(); }}
      onKeyDown={(event) => {
        if (event.key !== 'Tab') return;
        const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), a[href], [tabindex]',
        )).filter((node) => node.tabIndex >= 0 && node.getClientRects().length > 0);
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }}>
      <header className={styles.header}>
        <h2 id={titleId}>{title}</h2>
        <button type="button" className={styles.close} onClick={onClose} aria-label={`Close ${title}`}>Close</button>
      </header>
      {description && <p id={descriptionId} className={styles.description}>{description}</p>}
      <div className={styles.content}>{children}</div>
    </dialog>
  );
}
