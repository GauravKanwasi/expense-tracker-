import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import RecurringPanel from "./RecurringPanel";

describe("RecurringPanel", () => {
  it("shows a saved schedule and generates due entries on demand", async () => {
    const user = userEvent.setup();
    const onGenerate = vi.fn();

    render(
      <RecurringPanel
        recurring={[{
          id: 1,
          category_id: 1,
          amount: "499.99",
          type: "expense",
          description: "Music subscription",
          frequency: "monthly",
          next_due_at: "2026-09-10T03:30:00Z",
          active: true
        }]}
        categories={[{ id: 1, name: "Subscriptions" }]}
        form={{
          category_id: "1", amount: "", type: "expense", description: "",
          debt_direction: "borrowed", interest_amount: "", investment_action: "contribution",
          frequency: "monthly", next_due_at: "2026-09-10T09:00", active: true
        }}
        actionLoading=""
        onFormChange={vi.fn()}
        onSubmit={vi.fn()}
        onGenerate={onGenerate}
        onToggle={vi.fn()}
        onDelete={vi.fn()}
      />
    );

    expect(screen.getByText("Music subscription")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Generate due entries" }));
    expect(onGenerate).toHaveBeenCalledOnce();
  });
});
