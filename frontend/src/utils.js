export const emptyData = {
  summary: {
    total_income: 0,
    total_expenses: 0,
    balance: 0,
    cash_balance: 0,
    budget_total: 0,
    budget_spent: 0,
    budget_remaining: 0,
    available_after_budgets: 0,
    debt_borrowed: 0,
    debt_lent: 0,
    debt_interest: 0,
    investment_contributions: 0,
    investment_withdrawals: 0
  },
  categories: [],
  transactions: [],
  transactionTotal: 0,
  budgets: [],
  categoryTotals: []
};

export const STAT_ORDER_KEY = "ledgerly_stat_order";
export const STAT_IDS = ["balance", "income", "expenses", "available", "debt", "invested"];
export const TRANSACTIONS_PER_PAGE = 20;

export function localDateTime() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 16);
}

export function localDate(date) {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
}

export function blankTransaction(categoryId = "") {
  return {
    category_id: categoryId ? String(categoryId) : "",
    amount: "",
    type: "expense",
    debt_direction: "borrowed",
    interest_amount: "",
    investment_action: "contribution",
    description: "",
    date: localDateTime()
  };
}

export function formatMoney(value) {
  const cents = moneyToCents(value);
  const negative = cents < 0n;
  const absolute = negative ? -cents : cents;
  const whole = (absolute / 100n).toString();
  const fraction = (absolute % 100n).toString().padStart(2, "0");
  const groupedWhole = whole.length <= 3
    ? whole
    : whole.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",") +
      "," + whole.slice(-3);

  return `${negative ? "-" : ""}₹${groupedWhole}.${fraction}`;
}

export function moneyToCents(value) {
  const text = String(value ?? "0").trim().replace(/,/g, "");
  const negative = text.startsWith("-");
  const unsigned = negative ? text.slice(1) : text;
  const [wholePart = "0", fractionPart = ""] = unsigned.split(".");
  const whole = wholePart.replace(/\D/g, "") || "0";
  const fraction = fractionPart.replace(/\D/g, "").padEnd(2, "0").slice(0, 2);
  const cents = BigInt(whole) * 100n + BigInt(fraction || "0");

  return negative ? -cents : cents;
}

export function centsToMoney(cents) {
  const value = BigInt(cents);
  const negative = value < 0n;
  const absolute = negative ? -value : value;
  return `${negative ? "-" : ""}${absolute / 100n}.${(absolute % 100n)
    .toString()
    .padStart(2, "0")}`;
}

export function subtractMoney(left, right) {
  return centsToMoney(moneyToCents(left) - moneyToCents(right));
}

export function isNegativeMoney(value) {
  return moneyToCents(value) < 0n;
}

export function moneyPercent(value, maximum) {
  const amount = moneyToCents(value);
  const total = typeof maximum === "bigint"
    ? maximum
    : moneyToCents(maximum);

  if (amount <= 0n || total <= 0n) {
    return 0;
  }

  if (amount >= total) {
    return 100;
  }

  // BigInt keeps chart percentages correct for 29-digit values.
  return Number((amount * 10000n) / total) / 100;
}

export function isValidMoneyInput(value, allowZero = false) {
  const cents = moneyToCents(value);
  return /^\d{1,29}(\.\d{1,2})?$/.test(value) &&
    (allowZero ? cents >= 0n : cents > 0n);
}

export function sanitizeMoneyInput(value) {
  const cleaned = value.replace(/[^\d.]/g, "");
  const [wholePart = "", ...fractionParts] = cleaned.split(".");
  const whole = wholePart.slice(0, 29);

  if (!fractionParts.length) {
    return whole;
  }

  return `${whole}.${fractionParts.join("").slice(0, 2)}`;
}

export function formatDate(value) {
  if (!value) {
    return "No date";
  }

  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

export function transactionSign(transaction) {
  if (transaction.type === "expense") {
    return "-";
  }

  if (transaction.type === "income") {
    return "+";
  }

  if (transaction.type === "debt") {
    return transaction.debt_direction === "borrowed" ? "+" : "-";
  }

  return transaction.investment_action === "contribution" ? "-" : "+";
}

export function transactionLabel(transaction) {
  if (transaction.type === "debt") {
    return transaction.debt_direction === "borrowed"
      ? "Debt borrowed"
      : "Debt lent";
  }

  if (transaction.type === "investment") {
    return transaction.investment_action === "contribution"
      ? "Investment contribution"
      : "Investment withdrawal";
  }

  return transaction.type;
}

export function initials(name = "User") {
  return name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}
