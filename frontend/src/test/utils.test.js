import { describe, expect, it } from "vitest";
import {
  formatMoney,
  isValidMoneyInput,
  moneyToCents,
  sanitizeMoneyInput
} from "../utils";

describe("money helpers", () => {
  it("formats the documented 29-digit maximum without rounding", () => {
    const amount = "99999999999999999999999999999.99";

    expect(moneyToCents(amount)).toBe(9999999999999999999999999999999n);
    expect(formatMoney(amount)).toBe("₹99,99,99,99,99,99,99,99,99,99,99,99,99,999.99");
  });

  it("allows only positive values within the documented limit", () => {
    expect(isValidMoneyInput("0")).toBe(false);
    expect(isValidMoneyInput("0", true)).toBe(true);
    expect(isValidMoneyInput("100.50")).toBe(true);
    expect(isValidMoneyInput("1".repeat(30))).toBe(false);
  });

  it("keeps a typing-friendly money value", () => {
    expect(sanitizeMoneyInput("₹1,200.567")).toBe("1200.56");
  });
});
