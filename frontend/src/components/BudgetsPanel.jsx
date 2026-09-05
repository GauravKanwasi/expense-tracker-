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
  onFormChange,
  actionLoading,
  onSubmit,
  onDelete
}) {
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
          {actionLoading === "budget" ? "Saving..." : "Save monthly budget"}
        </button>
      </form>

      <div className="budget-list">
        {budgets.slice(0, 3).map((budget) => {
          const spent = budget.spent ?? "0";
          const remaining = budget.remaining ?? "0";
          const percentage = moneyPercent(spent, budget.amount);
          const overBudget = isNegativeMoney(remaining);

          return (
            <div className="budget-row" key={budget.id}>
              <div className="budget-row-top">
                <span>{budget.year}-{String(budget.month).padStart(2, "0")}</span>
                <strong>{formatMoney(budget.amount)}</strong>
                <button
                  className="icon-button"
                  onClick={() => onDelete(budget.id)}
                  disabled={actionLoading === "budget-" + budget.id}
                  aria-label="Delete budget"
                >
                  ×
                </button>
              </div>
              <div className="progress-track budget-progress">
                <span
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
    </article>
  );
}
