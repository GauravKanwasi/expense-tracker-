import {
  formatDate,
  formatMoney,
  transactionLabel,
  transactionSign
} from "../utils";
import { CardHeading, EmptyState } from "./ui";

export default function TransactionsPanel({
  transactions,
  total,
  categories,
  page,
  pageSize,
  actionLoading,
  onDelete,
  onAdd,
  onPageChange
}) {
  const categoryNames = Object.fromEntries(
    categories.map((category) => [category.id, category.name])
  );
  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  return (
    <section id="transactions" className="card section-card">
      <CardHeading
        eyebrow="ACTIVITY"
        title="Recent transactions"
        action={transactions.length + " of " + total + " shown"}
      />
      {transactions.length ? (
        <div className="transaction-list">
          <div className="transaction-header">
            <span>Transaction</span>
            <span>Category</span>
            <span>Date</span>
            <span className="align-right">Amount</span>
            <span />
          </div>
          <div className="transaction-scroll">
            {transactions.map((transaction) => (
              <div className="transaction-row" key={transaction.id}>
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
                <button
                  className="icon-button"
                  onClick={() => onDelete(transaction.id)}
                  disabled={actionLoading === "delete-" + transaction.id}
                  aria-label="Delete transaction"
                >
                  ×
                </button>
              </div>
            ))}
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
