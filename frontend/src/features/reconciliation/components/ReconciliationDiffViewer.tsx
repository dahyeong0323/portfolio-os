import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";
import type { ReconciliationSnapshot } from "../../../api/types";
import { DataTable, type DataColumn } from "../../../components/tables/DataTable";
import { StatusBadge } from "../../../components/status/StatusBadge";
import { formatDecimal } from "../../../lib/format";

interface DiffRow {
  id: string;
  label: string;
  expected: string;
  actual: string;
  difference: string;
  withinTolerance: boolean;
  context?: ReactNode;
}

const columns: DataColumn<DiffRow>[] = [
  { key: "label", header: "대상", render: (row) => <div><strong>{row.label}</strong>{row.context}</div> },
  { key: "expected", header: "Expected", align: "right", render: (row) => formatDecimal(row.expected) },
  { key: "actual", header: "Actual", align: "right", render: (row) => formatDecimal(row.actual) },
  { key: "difference", header: "차이", align: "right", render: (row) => formatDecimal(row.difference) },
  { key: "status", header: "판정", render: (row) => <StatusBadge label={row.withinTolerance ? "허용 범위" : "초과"} tone={row.withinTolerance ? "green" : "red"} /> },
];

function DiffSection({ title, rows }: { title: string; rows: DiffRow[] }) {
  return <section className="diff-section"><h3>{title}<span>{rows.length}</span></h3><DataTable columns={columns} rows={rows} rowKey={(row) => row.id} emptyMessage={`${title} 차이가 없습니다.`} caption={`${title} expected actual 차이`} /></section>;
}

export function ReconciliationDiffViewer({ reconciliation }: { reconciliation: ReconciliationSnapshot }) {
  const unresolved = reconciliation.actual_positions.filter((position) => position.match_status !== "matched");
  const positionRows = reconciliation.position_differences.map((row, index) => ({ id: `position-${index}`, label: row.symbol, expected: row.expected_quantity, actual: row.actual_quantity, difference: row.difference, withinTolerance: row.within_tolerance, context: <small>계좌 {row.account_id}</small> }));
  const cashRows = reconciliation.cash_differences.map((row, index) => ({ id: `cash-${index}`, label: row.currency, expected: row.expected_amount, actual: row.actual_amount, difference: row.difference, withinTolerance: row.within_tolerance, context: <small>계좌 {row.account_id}</small> }));
  const liabilityRows = reconciliation.liability_differences.map((row, index) => ({ id: `liability-${index}`, label: row.liability_name, expected: row.expected_amount, actual: row.actual_amount, difference: row.difference, withinTolerance: row.within_tolerance, context: <small>{row.currency}</small> }));
  const taxRows = reconciliation.tax_reserve_differences.map((row, index) => ({ id: `tax-${index}`, label: `${row.tax_year} ${row.tax_type}`, expected: row.expected_amount, actual: row.actual_amount, difference: row.difference, withinTolerance: row.within_tolerance, context: <small>{row.currency}</small> }));

  return (
    <section className="panel reconciliation-workspace" aria-labelledby="diff-viewer-title">
      <div className="panel__header"><div><p className="eyebrow">STEP 4 · EXPECTED VS ACTUAL</p><h2 id="diff-viewer-title">차이 검토</h2></div><span>OVER TOLERANCE IS NEVER HIDDEN</span></div>
      {unresolved.length > 0 && <div className="unresolved-instruments"><AlertTriangle aria-hidden="true" /><div><strong>매칭되지 않은 종목</strong>{unresolved.map((position) => <p key={`${position.account_id}-${position.symbol}`}>{position.symbol} · {position.match_status} · {position.match_error ?? "확인 필요"}</p>)}</div></div>}
      <div className="diff-grid">
        <DiffSection title="포지션" rows={positionRows} />
        <DiffSection title="현금" rows={cashRows} />
        <DiffSection title="부채" rows={liabilityRows} />
        <DiffSection title="세금 준비금" rows={taxRows} />
      </div>
    </section>
  );
}
