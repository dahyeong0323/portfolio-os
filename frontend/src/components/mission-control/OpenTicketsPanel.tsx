import type { InstrumentListResponse, OrderTicketListResponse } from "../../api/types";
import { formatDateTime, formatMoney } from "../../lib/format";
import { isOpenTicket } from "../../lib/guards";
import { ticketStatusMap } from "../../lib/statusMap";
import { StatusBadge } from "../status/StatusBadge";

export function OpenTicketsPanel({ tickets, instruments }: { tickets?: OrderTicketListResponse; instruments?: InstrumentListResponse }) {
  const names = new Map(instruments?.instruments.map((item) => [item.instrument_id, item.symbol]));
  const open = tickets?.tickets.filter(isOpenTicket) ?? [];
  return <section className="panel open-tickets"><div className="panel__header"><div><p className="eyebrow">OPEN TICKETS</p><h2>열린 주문 티켓</h2></div></div>{open.length === 0 ? <div className="empty-state"><span>ALL CLEAR</span><p>검토 대기 중인 열린 티켓이 없습니다.</p></div> : <div className="ticket-cards">{open.slice(0, 4).map((ticket) => { const def = ticketStatusMap[ticket.status]; return <article key={ticket.order_ticket_id}><div><span className="mono">#TKT-{ticket.order_ticket_id}</span><StatusBadge label={def.label} tone={def.tone} /></div><strong>{ticket.side === "buy" ? "매수" : "매도"} · {names.get(ticket.instrument_id) ?? `ID ${ticket.instrument_id}`}</strong><p>{formatMoney(ticket.ticket_notional, ticket.currency)} · {formatDateTime(ticket.created_at)}</p></article>; })}</div>}</section>;
}
