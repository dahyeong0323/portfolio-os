import { FileSpreadsheet, FileUp, ShieldCheck } from "lucide-react";
import type { FormEvent } from "react";
import type { Account } from "../../../api/types";

export type SnapshotFileKind = "positions" | "cash" | "liabilities" | "taxReserves";
export type SnapshotFiles = Partial<Record<SnapshotFileKind, File>>;

const fileFields: Array<{ kind: SnapshotFileKind; name: string; label: string; hint: string }> = [
  { kind: "positions", name: "positions_file", label: "포지션 CSV", hint: "symbol, currency, quantity · 선택 exchange, instrument_id" },
  { kind: "cash", name: "cash_file", label: "현금 CSV", hint: "currency, amount" },
  { kind: "liabilities", name: "liabilities_file", label: "부채 CSV", hint: "liability_name, currency, current_amount" },
  { kind: "taxReserves", name: "tax_reserves_file", label: "세금 준비금 CSV", hint: "tax_year, tax_type, currency, reserved_amount" },
];

interface SnapshotImportStepProps {
  accounts: Account[];
  accountId: string;
  asOfDate: string;
  files: SnapshotFiles;
  disabled: boolean;
  pending: boolean;
  error: string | null;
  onAccountChange: (value: string) => void;
  onDateChange: (value: string) => void;
  onFileChange: (kind: SnapshotFileKind, file: File | undefined) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

export function SnapshotImportStep(props: SnapshotImportStepProps) {
  return (
    <section className="panel reconciliation-workspace" aria-labelledby="snapshot-import-title">
      <div className="panel__header">
        <div><p className="eyebrow">STEP 1 · EXTERNAL ACTUALS</p><h2 id="snapshot-import-title">외부 스냅샷 가져오기</h2></div>
        <span>CSV · UTF-8 · 파일당 5 MiB</span>
      </div>
      <form className="snapshot-import-form" onSubmit={props.onSubmit}>
        <div className="form-grid">
          <label className="field-label">
            <span>대상 계좌 *</span>
            <select value={props.accountId} onChange={(event) => props.onAccountChange(event.target.value)} disabled={props.disabled || props.pending}>
              <option value="">활성 계좌 선택</option>
              {props.accounts.filter((account) => account.is_active).map((account) => (
                <option key={account.account_id} value={account.account_id}>{account.account_name} · {account.institution_name}</option>
              ))}
            </select>
          </label>
          <label className="field-label">
            <span>기준일 *</span>
            <input type="date" value={props.asOfDate} onChange={(event) => props.onDateChange(event.target.value)} disabled={props.disabled || props.pending} />
          </label>
        </div>

        <fieldset className="snapshot-file-grid" disabled={props.disabled || props.pending}>
          <legend>스냅샷 CSV · 최소 1개 필수</legend>
          {fileFields.map((field) => (
            <label className={props.files[field.kind] ? "snapshot-file is-selected" : "snapshot-file"} key={field.kind}>
              <FileSpreadsheet aria-hidden="true" />
              <span><strong>{field.label}</strong><small>{field.hint}</small><em>{props.files[field.kind]?.name ?? "파일 선택"}</em></span>
              <input
                type="file"
                name={field.name}
                accept=".csv,text/csv"
                onChange={(event) => props.onFileChange(field.kind, event.target.files?.[0])}
              />
            </label>
          ))}
        </fieldset>

        <div className="authority-notice">
          <ShieldCheck aria-hidden="true" />
          <div><strong>외부 값은 actual 비교 자료입니다.</strong><p>가져온 값은 내부 레저나 <code>cash_balances</code>에 직접 삽입되지 않습니다.</p></div>
        </div>
        {props.error && <div className="inline-error" role="alert">{props.error}</div>}
        <div className="wizard-actions">
          <button className="primary-action" type="submit" disabled={props.disabled || props.pending}>
            <FileUp aria-hidden="true" />{props.pending ? "가져오는 중…" : "스냅샷 가져오기"}
          </button>
          {props.disabled && <span>Mock mode에서는 실제 파일 업로드를 사용할 수 없습니다.</span>}
        </div>
      </form>
    </section>
  );
}
