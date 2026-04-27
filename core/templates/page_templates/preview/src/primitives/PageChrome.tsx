// ============================================================================
// Page-chrome primitives: TitleBlock, NarrativePanel, ActionQueue.
// ============================================================================

import type { ActionItem } from "../mock/datasets.js";
import "./primitives.css";

export interface TitleBlockProps {
  eyebrow: string;
  title: string;
  subtitle?: string | undefined;
}

export function TitleBlock({ eyebrow, title, subtitle }: TitleBlockProps): JSX.Element {
  return (
    <div className="page-title-block">
      <span className="page-title-block__eyebrow">{eyebrow}</span>
      <h2 className="page-title-block__title">{title}</h2>
      {subtitle && <p className="page-title-block__sub">{subtitle}</p>}
    </div>
  );
}

export interface NarrativePanelProps {
  title: string;
  paragraphs: string[];
}

export function NarrativePanel({ title, paragraphs }: NarrativePanelProps): JSX.Element {
  return (
    <div className="narrative-panel">
      <h3 className="narrative-panel__title">{title}</h3>
      {paragraphs.map((p, i) => (
        <p key={i} className="narrative-panel__body">
          {p}
        </p>
      ))}
    </div>
  );
}

export interface ActionQueueProps {
  title: string;
  items: ActionItem[];
}

export function ActionQueue({ title, items }: ActionQueueProps): JSX.Element {
  return (
    <div className="action-queue">
      <h3 className="action-queue__title">{title}</h3>
      {items.map((item) => (
        <div key={item.id} className="action-item">
          <span className="action-item__title">{item.title}</span>
          <span className={`action-item__chip tone-${item.tone}`}>
            {item.impact} / {item.effort}
          </span>
          <span className="action-item__meta">
            {item.owner} · ETA {item.eta}
          </span>
        </div>
      ))}
    </div>
  );
}
