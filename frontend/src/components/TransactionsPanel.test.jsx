import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import TransactionsPanel from "./TransactionsPanel";

describe("TransactionsPanel", () => {
  it("updates and clears type/category filters", async () => {
    const user = userEvent.setup();
    const onFiltersChange = vi.fn();

    render(
      <TransactionsPanel
        transactions={[]}
        total={0}
        categories={[{ id: 7, name: "Food" }]}
        page={0}
        pageSize={20}
        actionLoading=""
        filters={{ type: "", category_id: "" }}
        onDelete={vi.fn()}
        onEdit={vi.fn()}
        onAdd={vi.fn()}
        onPageChange={vi.fn()}
        onFiltersChange={onFiltersChange}
      />
    );

    await user.selectOptions(screen.getByLabelText("Filter by transaction type"), "expense");
    await user.selectOptions(screen.getByLabelText("Filter by category"), "7");

    expect(onFiltersChange).toHaveBeenNthCalledWith(1, { type: "expense" });
    expect(onFiltersChange).toHaveBeenNthCalledWith(2, { category_id: "7" });
  });
});
