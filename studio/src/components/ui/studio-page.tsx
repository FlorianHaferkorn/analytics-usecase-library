'use client';

import { cloneElement, isValidElement, useId, type ButtonHTMLAttributes, type CSSProperties, type HTMLAttributes, type ReactNode } from 'react';
import Link from 'next/link';
import styles from './studio-page.module.css';

type Tone = 'default' | 'info' | 'success' | 'warning';

// ── Page shell ──────────────────────────────────────────────────────────────

export function StudioPage({
  children,
  fill = false,
  width = 'wide',
  style,
}: {
  children: ReactNode;
  fill?: boolean;
  width?: 'standard' | 'wide' | 'canvas';
  style?: CSSProperties;
}) {
  return (
    <div
      className={`${styles.page} ${styles[`page${width.charAt(0).toUpperCase()}${width.slice(1)}`]}${fill ? ` ${styles.pageFill}` : ''}`}
      style={style}
    >
      {children}
    </div>
  );
}

// ── Page header ──────────────────────────────────────────────────────────────

export function StudioPageHeader({
  eyebrow, title, description, badge, actions, tone = 'default', compact = false,
}: {
  eyebrow?: string; title: string; description: string;
  badge?: string; actions?: ReactNode; tone?: Tone;
  /** Tighter header for pages that lead with content rather than with the title. */
  compact?: boolean;
}) {
  return (
    <div className={`${styles.pageHeader}${compact ? ` ${styles.pageHeaderCompact}` : ''}`} data-tone={tone}>
      <div className={styles.headerCopy}>
        {eyebrow && (
          <span className={styles.eyebrow}>
            {eyebrow}
          </span>
        )}
        <div className={styles.titleRow}>
          <h1 className={`${styles.title}${compact ? ` ${styles.titleCompact}` : ''}`}>
            {title}
          </h1>
          {badge && (
            <span className={styles.badge}>
              {badge}
            </span>
          )}
        </div>
        <p className={styles.description}>{description}</p>
      </div>
      {actions && (
        <div className={styles.headerActions}>{actions}</div>
      )}
    </div>
  );
}

// ── Metric bar ───────────────────────────────────────────────────────────────

export function StudioMetricBar({ children }: { children: ReactNode }) {
  return (
    <div className={styles.metricBar}>
      {children}
    </div>
  );
}

export function StudioMetric({
  label, value, meta, tone = 'default', trend,
}: {
  label: string; value: string | number; meta?: string; tone?: Tone; trend?: string;
}) {
  const positive = trend?.startsWith('+');
  const negative = trend?.startsWith('−') || trend?.startsWith('-');
  return (
    <div className={styles.metric} data-tone={tone}>
      <div className={styles.metricLabel}>{label}</div>
      <div className={styles.metricValueRow}>
        <span className={styles.metricValue}>
          {value}
        </span>
        {trend && (
          <span className={`${styles.metricTrend}${positive ? ` ${styles.metricTrendPositive}` : negative ? ` ${styles.metricTrendNegative}` : ''}`}>
            {trend}
          </span>
        )}
      </div>
      {meta && <div className={styles.metricMeta}>{meta}</div>}
    </div>
  );
}

// ── Panel ─────────────────────────────────────────────────────────────────────

export function StudioPanel({
  title, description, action, children, tone = 'default', style,
  compactHeader = false, bare = false, surface = 'outlined',
}: {
  title?: string; description?: string; action?: ReactNode;
  children: ReactNode; tone?: Tone; style?: CSSProperties;
  /** Slimmer header row — for panels that mostly hold a canvas, not prose. */
  compactHeader?: boolean;
  /** Drop the body padding so a full-bleed child (graph, table, editor) can fill it. */
  bare?: boolean;
  /** Visual hierarchy without inventing per-page card treatments. */
  surface?: 'plain' | 'outlined' | 'elevated';
}) {
  const hasHeader = !!(title || description || action);

  return (
    <section className={`${styles.panel} ${styles[`panel${surface.charAt(0).toUpperCase()}${surface.slice(1)}`]}`} data-tone={tone} style={style}>
      {hasHeader && (
        <div className={`${styles.panelHeader}${compactHeader ? ` ${styles.panelHeaderCompact}` : ''}`}>
          <div className={styles.panelCopy}>
            {title && <h3 className={styles.panelTitle}>{title}</h3>}
            {description && <p className={styles.panelDescription}>{description}</p>}
          </div>
          {action && <div className={styles.panelAction}>{action}</div>}
        </div>
      )}
      <div className={`${styles.panelBody}${bare ? ` ${styles.panelBodyBare}` : ''}`}>
        {children}
      </div>
    </section>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

export function StudioEmptyState({ title, description }: { title: string; description: ReactNode }) {
  return (
    <div className={styles.emptyState}>
      <p className={styles.emptyTitle}>{title}</p>
      <div className={styles.emptyDescription}>{description}</div>
    </div>
  );
}

// ── Toolbar ───────────────────────────────────────────────────────────────────

export function StudioToolbar({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div className={styles.toolbar} style={style}>
      {children}
    </div>
  );
}

// ── Workflow footer ───────────────────────────────────────────────────────────

/**
 * Closing "next step" link of a workflow page.
 *
 * The Studio modules form an ordered path (compose → simulate → generate → deliver →
 * templates); this makes the next hop explicit at the bottom of each page so the sidebar
 * is not the only way forward.
 */
export function StudioWorkflowFooter({
  label, href, description,
}: {
  label: string; href: string; description?: string;
}) {
  return (
    <div className={styles.workflowFooter}>
      {description
        ? <p className={styles.workflowDescription}>{description}</p>
        : <span />}
      <Link
        href={href}
        className={styles.workflowLink}
      >
        {label}
        <span aria-hidden="true">→</span>
      </Link>
    </div>
  );
}

// ── Button ────────────────────────────────────────────────────────────────────

export function StudioButton({
  children, variant = 'secondary', tone = 'default', type = 'button', className, ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  tone?: Tone;
  variant?: 'primary' | 'secondary' | 'ghost' | 'accent';
}) {
  const appearanceClass = {
    primary: styles.buttonPrimary,
    accent: styles.buttonAccent,
    secondary: styles.buttonSecondary,
    ghost: styles.buttonGhost,
  }[variant];

  return (
    <button
      {...props}
      type={type}
      data-tone={tone}
      className={`studio-button ${styles.button} ${appearanceClass}${className ? ` ${className}` : ''}`}
    >
      {children}
    </button>
  );
}

export function StudioLinkButton({
  href, children, variant = 'secondary', tone = 'default', className,
}: {
  href: string;
  children: ReactNode;
  tone?: Tone;
  variant?: 'primary' | 'secondary' | 'ghost' | 'accent';
  className?: string;
}) {
  const appearanceClass = {
    primary: styles.buttonPrimary,
    accent: styles.buttonAccent,
    secondary: styles.buttonSecondary,
    ghost: styles.buttonGhost,
  }[variant];
  return (
    <Link
      href={href}
      data-tone={tone}
      className={`studio-button ${styles.button} ${appearanceClass}${className ? ` ${className}` : ''}`}
    >
      {children}
    </Link>
  );
}

// ── Segmented control ─────────────────────────────────────────────────────────

export function StudioSegmentedControl<T extends string>({
  value, options, onChange, tone = 'default', className, onKeyDown, ...props
}: {
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (value: T) => void;
  tone?: Tone;
} & Omit<HTMLAttributes<HTMLDivElement>, 'onChange'>) {
  const selectedIndex = Math.max(0, options.findIndex((option) => option.value === value));
  return (
    <div
      {...props}
      role="group"
      aria-label={props['aria-labelledby'] ? undefined : (props['aria-label'] ?? 'View options')}
      data-tone={tone}
      className={`${styles.segmented}${className ? ` ${className}` : ''}`}
      onKeyDown={(event) => {
        onKeyDown?.(event);
        if (event.defaultPrevented || !options.length) return;
        const direction = event.currentTarget.ownerDocument.defaultView?.getComputedStyle(event.currentTarget).direction;
        const step = direction === 'rtl' ? -1 : 1;
        const target = event.key === 'ArrowRight' ? selectedIndex + step
          : event.key === 'ArrowLeft' ? selectedIndex - step
          : event.key === 'Home' ? 0
          : event.key === 'End' ? options.length - 1 : null;
        if (target === null) return;
        event.preventDefault();
        const index = (target + options.length) % options.length;
        onChange(options[index].value);
        event.currentTarget.querySelectorAll<HTMLButtonElement>('button')[index]?.focus();
      }}
    >
      {options.map((opt, index) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            aria-pressed={active}
            tabIndex={index === selectedIndex ? 0 : -1}
            className={`studio-button ${styles.segmentButton}${active ? ` ${styles.segmentButtonActive}` : ''}`}
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

// ── Form field ────────────────────────────────────────────────────────────────

export function StudioField({ label, children }: { label: string; children: ReactNode }) {
  const generatedId = useId();
  const control = isValidElement<{ id?: string; 'aria-labelledby'?: string }>(children) ? children : null;
  const controlId = control?.props.id ?? generatedId;
  const labelId = `${generatedId}-label`;
  return (
    <div className={styles.field}>
      <label id={labelId} htmlFor={controlId} className={styles.fieldLabel}>
        {label}
      </label>
      {control ? cloneElement(control, {
        id: controlId,
        'aria-labelledby': [labelId, control.props['aria-labelledby']].filter(Boolean).join(' '),
      }) : children}
    </div>
  );
}
