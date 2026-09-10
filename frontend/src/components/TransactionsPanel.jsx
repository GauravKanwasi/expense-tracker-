import {
  formatDate,
  formatMoney,
  transactionLabel,
  transactionSign
} from "../utils";
import { AnimatePresence, useReducedMotion } from "motion/react";
import * as m from "motion/react-m";
import { CardHeading, EmptyState } from "./ui";

export default function TransactionsPanel({
  transactions,
  total,
  categories,
  page,
  pageSize,
  actionLoading,
  filters,
  onDelete,
  onEdit,
  onAdd,
  onPageChange,
  onFiltersChange
}) {
  const categoryNames = Object.fromEntries(
    categories.map((category) => [category.id, category.name])
  );
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const shouldReduceMotion = useReducedMotion();

  return (
    <section id="transactions" className="card section-card">
      <CardHeading
        eyebrow="ACTIVITY"
        title="Recent transactions"
        action={transactions.length + " of " + total + " shown"}
      />
      <div className="transaction-filters" aria-label="Filter transactions">
        <select
          value={filters.type}
          onChange={(event) => onFiltersChange({ type: event.target.value })}
          aria-label="Filter by transaction type"
        >
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expenses</option>
          <option value="debt">Debt</option>
          <option value="investment">Investments</option>
        </select>
        <select
          value={filters.category_id}
          onChange={(event) => onFiltersChange({ category_id: event.target.value })}
          aria-label="Filter by category"
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
        {(filters.type || filters.category_id) && (
          <button
            type="button"
            className="text-button"
            onClick={() => onFiltersChange({ type: "", category_id: "" })}
          >
            Clear filters
          </button>
        )}
      </div>
      {transactions.length ? (
        <div className="transaction-list">
          <div className="transaction-header">
            <span>Transaction</span>
            <span>Category</span>
            <span>Date</span>
            <span className="align-right">Amount</span>
            <span className="align-right">Actions</span>
          </div>
          <div className="transaction-scroll">
            <AnimatePresence initial={false}>
              {transactions.map((transaction, motionIndex) => (
              <m.div
                layout="position"
                className="transaction-row"
                key={transaction.id}
                initial={shouldReduceMotion ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -6 }}
                whileHover={shouldReduceMotion ? undefined : { x: 4 }}
                transition={{
                  duration: shouldReduceMotion ? 0 : 0.18,
                  delay: shouldReduceMotion ? 0 : Math.min(motionIndex, 5) * 0.035
                }}
              >
                <div className="transaction-name">
                  <span className={"transaction-icon " + transaction.type}>
                    {transactionSign(transaction)}
                  </span>
                  <span>
                    <strong>{transaction.description || "Untitled transaction"}</strong>
                    <small>{transactionLabel(transaction)}</small>
                  </span>
                </div>
                <span className="category-pill">
                  {categoryNames[transaction.category_id] || "Unknown category"}
                </span>
                <span className="transaction-date">{formatDate(transaction.date)}</span>
                <strong className={"transaction-amount " + transaction.type}>
                  {transactionSign(transaction)}{formatMoney(transaction.amount)}
                </strong>
                <div className="row-actions">
                  <button
                    className="text-button"
                    onClick={() => onEdit(transaction)}
                    disabled={actionLoading === "delete-" + transaction.id}
                  >
                    Edit
                  </button>
                  <button
                    className="icon-button"
                    onClick={() => onDelete(transaction.id)}
                    disabled={actionLoading === "delete-" + transaction.id}
                    aria-label="Delete transaction"
                  >
                    ×
                  </button>
                </div>
              </m.div>
              ))}
            </AnimatePresence>
          </div>
          {total > pageSize && (
            <div className="pagination-controls">
              <button
                className="button button-small button-ghost"
                onClick={() => onPageChange(Math.max(0, page - 1))}
                disabled={page === 0}
              >
                Previous
              </button>
              <span>Page {page + 1} of {pageCount}</span>
              <button
                className="button button-small button-ghost"
                onClick={() => onPageChange(page + 1)}
                disabled={page + 1 >= pageCount}
              >
                Next
              </button>
            </div>
          )}
        </div>
      ) : (
        <EmptyState
          title="Your activity will appear here"
          copy="Add your first income, expense, debt, or investment to start your ledger."
          action={<button className="button button-primary" onClick={onAdd}>Add first transaction</button>}
        />
      )}
    </section>
  );
}
