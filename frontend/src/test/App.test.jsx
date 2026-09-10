import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  TOKEN_KEY: "expense_token",
  getCurrentUser: vi.fn(),
  getCategories: vi.fn(),
  getTransactions: vi.fn(),
  getSummary: vi.fn(),
  getCategoryTotals: vi.fn(),
  getBudgets: vi.fn(),
  getRecurringTransactions: vi.fn(),
  logout: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  createTransaction: vi.fn(),
  updateTransaction: vi.fn(),
  createCategory: vi.fn(),
  updateCategory: vi.fn(),
  createBudget: vi.fn(),
  updateBudget: vi.fn(),
  deleteTransaction: vi.fn(),
  deleteCategory: vi.fn(),
  deleteBudget: vi.fn()
}));

vi.mock("../api", () => api);

import App from "../App";

const summary = {
  total_income: "0.00",
  total_expenses: "0.00",
  balance: "0.00",
  cash_balance: "0.00",
  budget_total: "0.00",
  budget_spent: "0.00",
  budget_remaining: "0.00",
  available_after_budgets: "0.00",
  debt_borrowed: "0.00",
  debt_lent: "0.00",
  debt_interest: "0.00",
  investment_contributions: "0.00",
  investment_withdrawals: "0.00",
  budget_scope: "all_time"
};

describe("App", () => {
  beforeEach(() => {
    localStorage.setItem(api.TOKEN_KEY, "test-token");
    api.getCurrentUser.mockResolvedValue({ name: "Sapna", email: "sapna@example.com" });
    api.getCategories.mockResolvedValue([]);
    api.getTransactions.mockResolvedValue({ items: [], total: 0 });
    api.getSummary.mockResolvedValue(summary);
    api.getCategoryTotals.mockResolvedValue([]);
    api.getBudgets.mockResolvedValue([]);
    api.getRecurringTransactions.mockResolvedValue([]);
    api.logout.mockResolvedValue({ message: "Logged out successfully" });
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("clears the session when the user logs out", async () => {
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => expect(api.getCurrentUser).toHaveBeenCalledOnce());
    await user.click(screen.getAllByRole("button", { name: "Log out" })[0]);

    await waitFor(() => {
      expect(api.logout).toHaveBeenCalledOnce();
      expect(localStorage.getItem(api.TOKEN_KEY)).toBeNull();
    });
    expect(screen.getByRole("heading", { name: "Sign in to Ledgerly" })).toBeVisible();
  });
});
