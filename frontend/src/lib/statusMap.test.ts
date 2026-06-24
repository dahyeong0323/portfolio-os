import { describe, expect, it } from "vitest";
import { ledgerStatusMap, reconciliationStatusMap, ticketStatusMap } from "./statusMap";

describe("status maps", () => {
  it("maps ledger authority states to Korean labels and distinct tones", () => {
    expect(ledgerStatusMap.reconciled).toMatchObject({ label: "정상", tone: "green" });
    expect(ledgerStatusMap.broken).toMatchObject({ label: "불일치", tone: "red" });
  });

  it("covers every documented ticket status", () => {
    expect(Object.keys(ticketStatusMap)).toHaveLength(9);
    expect(reconciliationStatusMap.none.label).toBe("기록 없음");
  });
});
