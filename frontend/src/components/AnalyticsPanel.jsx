import {
  formatMoney,
  isNegativeMoney,
  moneyPercent,
  moneyToCents,
  subtractMoney
} from "../utils";
import { CardHeading, EmptyState, StatCard } from "./ui";

export default function AnalyticsPanel({
  summary,
  categoryTotals,
  children,
  statOrder,
  draggedStat,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd
}) {
  const maximumCategoryTotal = categoryTotals.reduce(
    (maximum, item) => {
      const total = moneyToCents(item.total);
      return total > maximum ? total : maximum;
    },
    1n
  );
  const statCards = {
    balance: {
      label: "Current balance",
      value: formatMoney(summary.cash_balance),
      note: "Cash after all movements",
      tone: isNegativeMoney(summary.cash_balance) ? "red" : "green",
      symbol: "="
    },
    income: {
      label: "Total income",
      value: formatMoney(summary.total_income),
      note: "Money coming in",
      tone: "blue",
      symbol: "+"
    },
    expenses: {
      label: "Total expenses",
      value: formatMoney(summary.total_expenses),
      note: "Money going out",
      tone: "orange",
      symbol: "−"
    },
    available: {
      label: "Available after plans",
      value: formatMoney(summary.available_after_budgets),
      note: "Cash minus unspent budgets",
      tone: isNegativeMoney(summary.available_after_budgets) ? "red" : "green",
      symbol: "P"
    },
    debt: {
      label: "Net debt",
      value: formatMoney(subtractMoney(summary.debt_borrowed, summary.debt_lent)),
      note: "Borrowed minus lent",
      tone: "purple",
      symbol: "D"
    },
    invested: {
      label: "Net invested",
      value: formatMoney(
        subtractMoney(summary.investment_contributions, summary.investment_withdrawals)
      ),
      note: "Contributions minus withdrawals",
      tone: "teal",
      symbol: "I"
    }
  };

  return (
    <>
      <section id="overview" className="stats-grid" aria-label="Financial summary">
        {statOrder.map((statId) => (
          <StatCard
            key={statId}
            statId={statId}
            draggedStat={draggedStat}
            onDragStart={onDragStart}
            onDragOver={onDragOver}
            onDrop={onDrop}
            onDragEnd={onDragEnd}
            {...statCards[statId]}
          />
        ))}
      </section>

      <section className="content-grid">
        <article className="card category-chart">
          <CardHeading
            eyebrow="SPENDING BREAKDOWN"
            title="Where your money goes"
            action={categoryTotals.length ? "Expenses only" : ""}
          />
          {categoryTotals.length ? (
            <div className="breakdown-list">
              {categoryTotals.map((item) => (
                <div className="breakdown-row" key={item.category_id}>
                  <div className="breakdown-label">
                    <span className="category-dot" />
                    <span>{item.category_name}</span>
                    <strong>{formatMoney(item.total)}</strong>
                  </div>
                  <div className="progress-track">
                    <span
                      className="progress-fill"
                      style={{ width: moneyPercent(item.total, maximumCategoryTotal) + "%" }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No expenses in this range"
              copy="Add an expense to see your spending pattern."
            />
          )}
        </article>
        {children}
      </section>
    </>
  );
}
