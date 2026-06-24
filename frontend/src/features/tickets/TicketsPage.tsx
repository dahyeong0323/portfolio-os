import { Link } from "react-router-dom";
import { useInstrumentsQuery } from "../../api/queries/instruments";
import { useTicketsQuery } from "../../api/queries/tickets";
import type { OrderTicket } from "../../api/types";
import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { StatusBadge } from "../../components/status/StatusBadge";
import { formatDateTime, formatDecimal, formatMoney } from "../../lib/format";
import { errorMessage } from "../../lib/guards";
import { ticketStatusMap } from "../../lib/statusMap";

export function TicketsPage() {
  const tickets = useTicketsQuery();
  const instruments = useInstrumentsQuery();
  const names = new Map(instruments.data?.instruments.map((item) => [item.instrument_id, item.symbol]));
  const columns: DataColumn<OrderTicket>[] = [
    { key: "id", header: "티켓", render: (row) => <Link className="table-link mono" to={`/tickets/${row.order_ticket_id}`}>#TKT-{row.order_ticket_id}</Link> },
    { key: "side", header: "방향", render: (row) => <StatusBadge label={row.side === "buy" ? "자산 편입 의도" : "자산 축소 의도"} tone={row.side === "buy" ? "cyan" : "violet"} /> },
    { key: "instrument", header: "종목", render: (row) => names.get(row.instrument_id) ?? `ID ${row.instrument_id}` },
    { key: "quantity", header: "수량", align: "right", render: (row) => formatDecimal(row.ticket_quantity) },
    { key: "notional", header: "금액", align: "right", render: (row) => formatMoney(row.ticket_notional, row.currency) },
    { key: "status", header: "상태", render: (row) => { const def = ticketStatusMap[row.status]; return <StatusBadge label={def.label} tone={def.tone} title={def.description} />; } },
    { key: "created", header: "생성 시각", render: (row) => formatDateTime(row.created_at) },
  ];
  return (
    <div className="page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">ORDER TICKET REGISTER</p>
          <h1>주문 티켓</h1>
          <p>Risk Engine 검증으로 생성된 공식 수동 주문 티켓을 조회합니다.</p>
        </div>
        <Link className="secondary-action" to="/risk">리스크 워크스페이스</Link>
      </header>
      {tickets.error && <div className="inline-error" role="alert">{errorMessage(tickets.error)}</div>}
      <section className="panel">
        <div className="panel__header"><div><p className="eyebrow">ALL TICKETS</p><h2>티켓 목록 <span>{tickets.data?.count ?? 0}</span></h2></div></div>
        <DataTable columns={columns} rows={tickets.data?.tickets ?? []} rowKey={(row) => row.order_ticket_id} emptyMessage="생성된 주문 티켓이 없습니다." caption="주문 티켓 목록" />
      </section>
      <section className="panel read-only-notice">
        <strong>Stage 4 검토 전용</strong>
        <p>이 티켓은 자동 주문이 아닙니다. 실제 주문은 사용자가 증권사 화면에서 수동으로 실행해야 합니다. 승인, 거절, 수정, 실행 기능은 제공하지 않습니다.</p>
      </section>
    </div>
  );
}
