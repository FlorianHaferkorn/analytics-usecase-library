// ============================================================================
// <DetailMatrix> — dense drill-in table with tone chips for variance.
// ============================================================================

import type { DriverRow } from "../mock/datasets.js";
import "./primitives.css";

export interface DetailMatrixProps {
  title: string;
  rows: DriverRow[];
  actualLabel?: string | undefined;
  planLabel?: string | undefined;
  formatValue?: ((v: number) => string) | undefined;
}

export function DetailMatrix({
  title,
  rows,
  actualLabel = "Actual",
  planLabel = "Plan",
  formatValue = (v) => (Math.abs(v) >= 1000 ? v.toLocaleString("en-US") : v.toFixed(1)),
}: DetailMatrixProps): JSX.Element {
  return (
    <div className="detail-matrix">
      <header className="detail-matrix__header">
        <h3 className="detail-matrix__title">{title}</h3>
      </header>
      <div className="detail-matrix__scroll">
        <table>
          <thead>
            <tr>
              <th>Driver</th>
              <th className="detail-matrix__num">{actualLabel}</th>
              <th className="detail-matrix__num">{planLabel}</th>
              <th className="detail-matrix__num">Δ</th>
              <th className="detail-matrix__num">Δ%</th>
              <th>Owner</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const sign = row.variancePct >= 0 ? "+" : "";
              return (
                <tr key={row.id}>
                  <td>{row.name}</td>
                  <td className="detail-matrix__num">{formatValue(row.actual)}</td>
                  <td className="detail-matrix__num">{formatValue(row.plan)}</td>
                  <td className="detail-matrix__num">
                    <span className={`detail-matrix__chip tone-${row.tone}`}>
                      {row.varianceAbs >= 0 ? "+" : ""}
                      {formatValue(row.varianceAbs)}
                    </span>
                  </td>
                  <td className="detail-matrix__num">
                    {sign}
                    {(row.variancePct * 100).toFixed(1)}%
                  </td>
                  <td>{row.owner}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
