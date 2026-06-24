import { usePostmortemTasks } from "../../api/queries/postmortems";
import type { PostmortemTask } from "../../api/types";
import { StatusBadge } from "../../components/status/StatusBadge";
import { DataTable, type DataColumn } from "../../components/tables/DataTable";
import { formatDate, formatDateTime } from "../../lib/format";
import { errorMessage } from "../../lib/guards";

function linkedTarget(row: PostmortemTask) {
  if (row.override_ticket_id) return `OVR-${row.override_ticket_id}`;
  if (row.order_ticket_id) return `TKT-${row.order_ticket_id}`;
  return "-";
}

export function PostmortemsPage() {
  const postmortems = usePostmortemTasks();
  const columns: DataColumn<PostmortemTask>[] = [
    { key: "id", header: "Task", render: (row) => <span className="mono">#PM-{row.postmortem_task_id}</span> },
    { key: "status", header: "상태", render: (row) => <StatusBadge label={row.status} tone={row.status === "scheduled" ? "amber" : "gray"} /> },
    { key: "link", header: "연결", render: linkedTarget },
    { key: "due", header: "기한", render: (row) => formatDate(row.due_date) },
    { key: "questions", header: "질문", render: (row) => row.prompt_questions.join(" / ") },
    { key: "created", header: "생성", render: (row) => formatDateTime(row.created_at) },
  ];
  return (
    <div className="page postmortems-page">
      <header className="page-heading">
        <div>
          <p className="eyebrow">POSTMORTEM QUEUE</p>
          <h1>복기 태스크</h1>
          <p>예외와 중요한 결정을 나중에 다시 읽기 위한 감사 queue입니다. 완료 기록은 후속 단계입니다.</p>
        </div>
        <span className="read-only-tag">RECORDING DEFERRED</span>
      </header>
      {postmortems.error ? <div className="inline-error" role="alert">{errorMessage(postmortems.error)}</div> : null}
      <section className="panel">
        <div className="panel__header"><div><p className="eyebrow">TASKS</p><h2>대기 중인 복기 <span>{postmortems.data?.count ?? 0}</span></h2></div></div>
        <DataTable columns={columns} rows={postmortems.data?.tasks ?? []} rowKey={(row) => row.postmortem_task_id} emptyMessage="대기 중인 복기 태스크가 없습니다." caption="복기 태스크" />
      </section>
    </div>
  );
}
