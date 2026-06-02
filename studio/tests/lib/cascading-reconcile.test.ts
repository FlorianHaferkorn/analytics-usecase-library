import { describe, it, expect } from 'vitest';
import {
  extractFactsheetKpiRoles,
  reconcileDeterministic,
} from '@/lib/studio/cascading-reconcile';

const SAMPLE_BRACKET = `
orchestration:
  strategic_kpi_id: margin.gm.pct
  influencing_kpi_ids:
    - sales.net_sales.amount
  action_code_ids:
    - C-S1.1
`.trim();

const SAMPLE_FACTSHEET = `
### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| margin.gm.pct | Strategic |
| sales.net_sales.amount | Influencing |
| cost.cogs.amount | Influencing |

**Action Codes:** C-S1.1, C-S1.2
`.trim();

describe('extractFactsheetKpiRoles', () => {
  it('parses single-pipe markdown table rows', () => {
    const roles = extractFactsheetKpiRoles(SAMPLE_FACTSHEET);
    const ids = roles.map((r) => r.kpi_id);
    expect(ids).toContain('margin.gm.pct');
    expect(ids).toContain('cost.cogs.amount');
  });
});

describe('reconcileDeterministic (factsheet → bracket)', () => {
  it('clears influencing_kpi_ids when factsheet table has none', () => {
    const factsheet = `
### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| margin.gm.pct | Strategic |

**Action Codes:** C-S1.1
`.trim();

    const proposal = reconcileDeterministic({
      editedSource: 'factsheet',
      prose: factsheet,
      bracketYaml: SAMPLE_BRACKET,
    });

    expect(proposal).not.toBeNull();
    expect(proposal?.patch).not.toContain('sales.net_sales.amount');
    expect(proposal?.hints.some((h) => h.includes('Clear influencing_kpi_ids'))).toBe(true);
  });

  it('replaces action_code_ids from factsheet instead of merging', () => {
    const factsheet = `
### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| margin.gm.pct | Strategic |
| sales.net_sales.amount | Influencing |

**Action Codes:** C-S1.2
`.trim();

    const proposal = reconcileDeterministic({
      editedSource: 'factsheet',
      prose: factsheet,
      bracketYaml: SAMPLE_BRACKET,
    });

    expect(proposal?.patch).toContain('- C-S1.2');
    expect(proposal?.patch).not.toContain('- C-S1.1');
  });
});
