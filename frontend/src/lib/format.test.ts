import { describe, expect, it } from "vitest";
import { formatDecimal, formatMoney } from "./format";

describe("decimal string formatting", () => {
  it("groups integer digits without converting through a floating point number", () => {
    expect(formatDecimal("12345678901234567890.120000")).toBe("12,345,678,901,234,567,890.12");
  });

  it("keeps currency rendering string based", () => {
    expect(formatMoney("0001250.50", "CHF")).toBe("0,001,250.5 CHF");
  });
});
