import type { ReactNode } from "react";

export interface DataColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  align?: "left" | "right";
}

interface DataTableProps<T> {
  columns: DataColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  emptyMessage: string;
  caption: string;
}

export function DataTable<T>({ columns, rows, rowKey, emptyMessage, caption }: DataTableProps<T>) {
  if (rows.length === 0) return <div className="empty-state"><span>NO DATA</span><p>{emptyMessage}</p></div>;
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <caption className="sr-only">{caption}</caption>
        <thead><tr>{columns.map((column) => <th key={column.key} className={column.align === "right" ? "align-right" : undefined}>{column.header}</th>)}</tr></thead>
        <tbody>{rows.map((row) => <tr key={rowKey(row)}>{columns.map((column) => <td key={column.key} className={column.align === "right" ? "align-right mono" : undefined}>{column.render(row)}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}
