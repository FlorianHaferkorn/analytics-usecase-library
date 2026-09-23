'use client';

import Link from 'next/link';
import styles from './delivery-model-3d.module.css';

export type DeliveryStageState = 'not_recorded' | 'recorded' | 'active' | 'blocked' | 'complete';

export interface DeliveryStage {
  step: string;
  title: string;
  outcome: string;
  href: string;
  state: DeliveryStageState;
  definition: boolean;
  delivery: boolean;
  evidence: boolean;
}

const stateLabel: Record<DeliveryStageState, string> = {
  not_recorded: 'Not recorded',
  recorded: 'Recorded',
  active: 'In progress',
  blocked: 'Blocked',
  complete: 'Complete',
};

export function DeliveryModel3D({ stages }: { stages: DeliveryStage[] }) {
  return <section className={styles.shell} aria-labelledby="delivery-model-title">
    <header className={styles.header}>
      <div>
        <p className={styles.eyebrow}>Project delivery model</p>
        <h2 id="delivery-model-title">One path from evidence to verified operation</h2>
        <p className={styles.lead}>Move left to right. Each stage must connect a governed definition, delivery work and retained evidence.</p>
      </div>
      <div className={styles.axisKey} aria-label="Model dimensions">
        <span><i className={styles.axisX} /> X · lifecycle</span>
        <span><i className={styles.axisY} /> Depth · project layer</span>
        <span><i className={styles.axisZ} /> Height · maturity</span>
      </div>
    </header>

    <div className={styles.viewport}>
      <div className={styles.floor} aria-hidden="true" />
      <ol className={styles.stages}>
        {stages.map((stage) => <li key={stage.step} className={styles.stage} data-state={stage.state}>
          <Link href={stage.href} className={styles.volume} aria-label={`${stage.title}: ${stateLabel[stage.state]}`}>
            <span className={styles.step}>{stage.step}</span>
            <span className={styles.state}>{stateLabel[stage.state]}</span>
            <strong>{stage.title}</strong>
            <small>{stage.outcome}</small>
          </Link>
          <div className={styles.layers} aria-label={`${stage.title} project layers`}>
            <span data-ready={stage.definition}>Definition</span>
            <span data-ready={stage.delivery}>Delivery</span>
            <span data-ready={stage.evidence}>Evidence</span>
          </div>
        </li>)}
      </ol>
    </div>

    <footer className={styles.footer}>
      <p><strong>How to read it:</strong> a raised stage has a recorded basis. Orange requires action; red is blocked. The three depth markers prevent a design document from being mistaken for delivery or evidence.</p>
      <div className={styles.legend} aria-label="Status legend"><span data-state="complete">Complete</span><span data-state="active">In progress</span><span data-state="blocked">Blocked</span><span data-state="recorded">Recorded</span></div>
    </footer>
  </section>;
}
