import {
  formatDate,
  formatMoney,
  sanitizeMoneyInput,
  transactionLabel,
  transactionSign
} from "../utils";
import { AnimatePresence, useReducedMotion } from "motion/react";
import * as m from "motion/react-m";
import { CardHeading } from "./ui";

export default function RecurringPanel({
  recurring,
  categories,
  form,
  actionLoading,
  onFormChange,
  onSubmit,
  onGenerate,
  onToggle,
  onDelete
}) {
  const updateForm = (field, value) => onFormChange({ ...form, [field]: value });
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="recurring" className="card section-card">
      <CardHeading
        eyebrow="AUTOMATION"
        title="Recurring schedules"
        action={recurring.length + " saved"}
      />
      <form className="recurring-form" onSubmit={onSubmit}>
        <div className="recurring-grid">
          <label>
            Type
            <select value={form.type} onChange={(event) => updateForm("type", event.target.value)}>
              <option value="expense">Expense</option>
              <option value="income">Income</option>
              <option value="debt">Debt</option>
              <option value="investment">Investment</option>
            </select>
          </label>
          <label>
            Repeat
            <select value={form.frequency} onChange={(event) => updateForm("frequency", event.target.value)}>
              <option value="monthly">Monthly</option>
              <option value="weekly">Weekly</option>
            </select>
          </label>
          <label>
            Category
            <select value={form.category_id} onChange={(event) => updateForm("category_id", event.target.value)} required>
              <option value="">Select a category</option>
              {categories.map((category) => (
                <option value={category.id} key={category.id}>{category.name}</option>
              ))}
            </select>
          </label>
          <label>
            Next due
            <input
              type="datetime-local"
              value={form.next_due_at}
              onChange={(event) => updateForm("next_due_at", event.target.value)}
              required
            />
          </label>
          <label>
            Amount
            <input
              type="text"
              inputMode="decimal"
              maxLength="32"
              placeholder="0.00"
              value={form.amount}
              onChange={(event) => updateForm("amount", sanitizeMoneyInput(event.target.value))}
              required
            />
          </label>
          <label>
            Description
            <input
              type="text"
              maxLength="255"
              placeholder="Salary, rent, EMI…"
              value={form.description}
              onChange={(event) => updateForm("description", event.target.value)}
            />
          </label>
        </div>
        <AnimatePresence initial={false} mode="wait">
        {form.type === "debt" && (
          <m.div
            key="recurring-debt-details"
            className="recurring-grid detail-panel debt-panel"
            initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -6 }}
            transition={{ duration: shouldReduceMotion ? 0 : 0.18 }}
          >
            <label>
              Direction
              <select value={form.debt_direction} onChange={(event) => updateForm("debt_direction", event.target.value)}>
                <option value="borrowed">Borrowed money</option>
                <option value="lent">Money lent out</option>
              </select>
            </label>
            <label>
              Interest amount
              <input
                type="text"
                inputMode="decimal"
                maxLength="32"
                placeholder="Optional"
                value={form.interest_amount}
                onChange={(event) => updateForm("interest_amount", sanitizeMoneyInput(event.target.value))}
              />
            </label>
          </m.div>
        )}
        {form.type === "investment" && (
          <m.label
            key="recurring-investment-details"
            className="recurring-action"
            initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -6 }}
            transition={{ duration: shouldReduceMotion ? 0 : 0.18 }}
          >
              Investment action
              <select value={form.investment_action} onChange={(event) => updateForm("investment_action", event.target.value)}>
                <option value="contribution">Money invested</option>
                <option value="withdrawal">Money withdrawn</option>
              </select>
          </m.label>
        )}
        </AnimatePresence>
        <button className="button button-dark" disabled={!categories.length || actionLoading === "recurring"}>
          {actionLoading === "recurring" ? "Saving..." : "Save schedule"}
        </button>
      </form>

      <div className="recurring-heading">
        <strong>Due entries</strong>
        <button
          type="button"
          className="button button-small button-ghost"
          onClick={onGenerate}
          disabled={!recurring.some((rule) => rule.active) || actionLoading === "generate-recurring"}
        >
          {actionLoading === "generate-recurring" ? "Generating..." : "Generate due entries"}
        </button>
      </div>
      <div className="recurring-list">
        <AnimatePresence initial={false}>
        {recurring.map((rule, motionIndex) => (
          <m.div
            layout="position"
            className={"recurring-row" + (rule.active ? "" : " paused")}
            key={rule.id}
            initial={shouldReduceMotion ? false : { opacity: 0, y: 10, scale: 0.985 }}
            animate={{ opacity: rule.active ? 1 : 0.7, y: 0, scale: 1 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -8, scale: 0.985 }}
            whileHover={shouldReduceMotion ? undefined : { y: -2 }}
            transition={{
              duration: shouldReduceMotion ? 0 : 0.2,
              delay: shouldReduceMotion ? 0 : Math.min(motionIndex, 5) * 0.04
            }}
          >
            <span className={"transaction-icon " + rule.type}>{transactionSign(rule)}</span>
            <div>
              <strong>{rule.description || "Untitled schedule"}</strong>
              <small>{transactionLabel(rule)} · every {rule.frequency} · next {formatDate(rule.next_due_at)}</small>
            </div>
            <strong className={"transaction-amount " + rule.type}>
              {transactionSign(rule)}{formatMoney(rule.amount)}
            </strong>
            <div className="row-actions">
              <button
                type="button"
                className="text-button"
                onClick={() => onToggle(rule)}
                disabled={actionLoading === "recurring-" + rule.id}
              >
                {rule.active ? "Pause" : "Resume"}
              </button>
              <button
                type="button"
                className="icon-button"
                onClick={() => onDelete(rule.id)}
                disabled={actionLoading === "recurring-" + rule.id}
                aria-label="Delete recurring schedule"
              >
                ×
              </button>
            </div>
          </m.div>
        ))}
        </AnimatePresence>
        {!recurring.length && <p className="muted-copy">Save a schedule for repeat income, rent, subscriptions, or EMI payments.</p>}
      </div>
    </section>
  );
}
