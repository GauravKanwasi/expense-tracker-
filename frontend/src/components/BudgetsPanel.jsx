import { useState } from "react";
import {
  formatMoney,
  isNegativeMoney,
  moneyPercent,
  sanitizeMoneyInput,
  subtractMoney
} from "../utils";
import { CardHeading } from "./ui";

export default function BudgetsPanel({
  budgets,
  form,
  editing,
  onFormChange,
  actionLoading,
  onSubmit,
  onDelete,
  onEdit,
  onCancelEdit
}) {
  const [showAll, setShowAll] = useState(false);
  const visibleBudgets = showAll ? budgets : budgets.slice(0, 3);

  return (
    <article className="card budget-card">
      <CardHeading
        eyebrow="MONTHLY PLANS"
        title="Budgets"
        action={budgets.length + " saved"}
      />
      <form className="compact-form" onSubmit={onSubmit}>
        <div className="form-row">
          <label>
            Year
            <input
              type="number"
              min="2000"
              max="2100"
              value={form.year}
              onChange={(event) => onFormChange({ ...form, year: event.target.value })}
              required
            />
          </label>
          <label>
            Month
            <input
              type="number"
              min="1"
              max="12"
              value={form.month}
              onChange={(event) => onFormChange({ ...form, month: event.target.value })}
              required
            />
          </label>
          <label className="amount-field">
            Amount
            <input
              type="text"
              inputMode="decimal"
              maxLength="32"
              placeholder="10,000"
              value={form.amount}
              onChange={(event) => onFormChange({
                ...form,
                amount: sanitizeMoneyInput(event.target.value)
              })}
              required
            />
          </label>
        </div>
        <button
          className="button button-dark button-full"
          disabled={actionLoading === "budget"}
        >
          {actionLoading === "budget"
            ? "Saving..."
            : editing ? "Save budget changes" : "Save monthly budget"}
        </button>
        {editing && (
          <button type="button" className="button button-ghost button-full" onClick={onCancelEdit}>
            Cancel edit
          </button>
        )}
      </form>

      <div className="budget-list">
        {visibleBudgets.map((budget, motionIndex) => {
          const spent = budget.spent ?? "0";
          const remaining = budget.remaining ?? "0";
          const percentage = moneyPercent(spent, budget.amount);
          const overBudget = isNegativeMoney(remaining);

          return (
            <div
              className="budget-row"
              key={budget.id}
              style={{ "--motion-index": motionIndex }}
            >
              <div className="budget-row-top">
                <span>{budget.year}-{String(budget.month).padStart(2, "0")}</span>
                <strong>{formatMoney(budget.amount)}</strong>
                <div className="row-actions">
                  <button
                    className="text-button"
                    onClick={() => onEdit(budget)}
                    disabled={actionLoading === "budget-" + budget.id}
                  >
                    Edit
                  </button>
                  <button
                    className="icon-button"
                    onClick={() => onDelete(budget.id)}
                    disabled={actionLoading === "budget-" + budget.id}
                    aria-label="Delete budget"
                  >
                    ×
                  </button>
                </div>
              </div>
              <div className="progress-track budget-progress">
                <span
                  key={`${budget.id}-${spent}-${budget.amount}`}
                  className={"progress-fill " + (percentage > 85 ? "warning" : "")}
                  style={{ width: percentage + "%" }}
                />
              </div>
              <small className={overBudget ? "budget-over" : ""}>
                {formatMoney(spent)} spent · {formatMoney(
                  overBudget ? subtractMoney("0", remaining) : remaining
                )} {overBudget ? "over" : "remaining"}
              </small>
            </div>
          );
        })}
        {!budgets.length && (
          <p className="muted-copy">No budgets yet. Add your first monthly plan above.</p>
        )}
      </div>
      {budgets.length > 3 && (
        <button type="button" className="text-button budget-history-toggle" onClick={() => setShowAll((shown) => !shown)}>
          {showAll ? "Show recent budgets" : "Show all budget history (" + budgets.length + ")"}
        </button>
      )}
    </article>
  );
}
