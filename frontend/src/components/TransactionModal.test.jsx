import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import TransactionModal from "./TransactionModal";

const form = {
  category_id: "1",
  amount: "250.00",
  type: "expense",
  debt_direction: "borrowed",
  interest_amount: "",
  investment_action: "contribution",
  description: "Lunch",
  date: "2026-09-10T12:00"
};

describe("TransactionModal", () => {
  it("shows edit feedback and closes with Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <TransactionModal
        visible
        form={form}
        categories={[{ id: 1, name: "Food" }]}
        actionLoading=""
        editing={{ id: 2 }}
        error="Enter a valid amount."
        onFormChange={vi.fn()}
        onSubmit={vi.fn((event) => event.preventDefault())}
        onClose={onClose}
        onGoToCategories={vi.fn()}
      />
    );

    expect(screen.getByRole("dialog", { name: "Edit transaction" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a valid amount.");
    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledOnce();
  });
});
