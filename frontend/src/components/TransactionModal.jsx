import { sanitizeMoneyInput } from "../utils";
import { EmptyState } from "./ui";

export default function TransactionModal({
  visible,
  form,
  categories,
  actionLoading,
  onFormChange,
  onSubmit,
  onClose,
  onGoToCategories
}) {
  if (!visible) {
    return null;
  }

  const updateForm = (field, value) => onFormChange({ ...form, [field]: value });

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="transaction-title">
        <div className="modal-heading">
          <div>
            <p className="eyebrow">NEW ENTRY</p>
            <h2 id="transaction-title">Add transaction</h2>
          </div>
          <button className="icon-button close-button" onClick={onClose} aria-label="Close transaction form">
            ×
          </button>
        </div>
        {categories.length ? (
          <form className="modal-form" onSubmit={onSubmit}>
            <div className="type-toggle">
              {[
                ["expense", "Expense"],
                ["income", "Income"],
                ["debt", "Debt"],
                ["investment", "Investment"]
              ].map(([type, label]) => (
                <button
                  key={type}
                  type="button"
                  className={form.type === type ? "selected " + type : ""}
                  onClick={() => updateForm("type", type)}
                >
                  {label}
                </button>
              ))}
            </div>
            <label>
              Amount
              <div className="input-prefix">
                <span>₹</span>
                <input
                  type="text"
                  inputMode="decimal"
                  maxLength="32"
                  placeholder="0.00"
                  value={form.amount}
                  onChange={(event) => updateForm("amount", sanitizeMoneyInput(event.target.value))}
                  required
                />
              </div>
            </label>
            {form.type === "debt" && (
              <div className="detail-panel debt-panel">
                <label>
                  Debt direction
                  <select
                    value={form.debt_direction}
                    onChange={(event) => updateForm("debt_direction", event.target.value)}
                  >
                    <option value="borrowed">Borrowed money</option>
                    <option value="lent">Money lent out</option>
                  </select>
                </label>
                <label>
                  Interest amount
                  <div className="input-prefix">
                    <span>₹</span>
                    <input
                      type="text"
                      inputMode="decimal"
                      maxLength="32"
                      placeholder="Optional"
                      value={form.interest_amount}
                      onChange={(event) => updateForm(
                        "interest_amount",
                        sanitizeMoneyInput(event.target.value)
                      )}
                    />
                  </div>
                </label>
              </div>
            )}
            {form.type === "investment" && (
              <div className="detail-panel investment-panel">
                <label>
                  Investment action
                  <select
                    value={form.investment_action}
                    onChange={(event) => updateForm("investment_action", event.target.value)}
                  >
                    <option value="contribution">Money invested</option>
                    <option value="withdrawal">Money withdrawn</option>
                  </select>
                </label>
                <p>Investments stay separate from ordinary expenses.</p>
              </div>
            )}
            <label>
              Category
              <select
                value={form.category_id}
                onChange={(event) => updateForm("category_id", event.target.value)}
                required
              >
                <option value="">Select a category</option>
                {categories.map((category) => (
                  <option value={category.id} key={category.id}>{category.name}</option>
                ))}
              </select>
            </label>
            <label>
              Description
              <input
                type="text"
                maxLength="255"
                placeholder="What was this for?"
                value={form.description}
                onChange={(event) => updateForm("description", event.target.value)}
              />
            </label>
            <label>
              Date and time
              <input
                type="datetime-local"
                value={form.date}
                onChange={(event) => updateForm("date", event.target.value)}
                required
              />
            </label>
            <button className="button button-primary button-full" disabled={actionLoading === "transaction"}>
              {actionLoading === "transaction" ? "Adding..." : "Add transaction"}
            </button>
          </form>
        ) : (
          <EmptyState
            title="Create a category first"
            copy="Transactions need a category so your spending stays organized."
            action={<button className="button button-dark" onClick={onGoToCategories}>Go to categories</button>}
          />
        )}
      </div>
    </div>
  );
}
