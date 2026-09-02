import { useEffect, useState } from "react";
import * as api from "./api";
import "./styles.css";

const emptyData = {
  summary: {
    total_income: 0,
    total_expenses: 0,
    balance: 0,
    debt_borrowed: 0,
    debt_lent: 0,
    debt_interest: 0,
    investment_contributions: 0,
    investment_withdrawals: 0
  },
  categories: [],
  transactions: [],
  budgets: [],
  categoryTotals: []
};

function localDateTime() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 16);
}

function localDate(date) {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
}

function blankTransaction(categoryId = "") {
  return {
    category_id: categoryId ? String(categoryId) : "",
    amount: "",
    type: "expense",
    debt_direction: "borrowed",
    interest_amount: "",
    investment_action: "contribution",
    description: "",
    date: localDateTime()
  };
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(Number(value) || 0);
}

function formatDate(value) {
  if (!value) {
    return "No date";
  }

  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function transactionSign(transaction) {
  if (transaction.type === "expense") {
    return "-";
  }

  if (transaction.type === "income") {
    return "+";
  }

  if (transaction.type === "debt") {
    return transaction.debt_direction === "borrowed" ? "+" : "-";
  }

  return transaction.investment_action === "contribution" ? "-" : "+";
}

function transactionLabel(transaction) {
  if (transaction.type === "debt") {
    return transaction.debt_direction === "borrowed"
      ? "Debt borrowed"
      : "Debt lent";
  }

  if (transaction.type === "investment") {
    return transaction.investment_action === "contribution"
      ? "Investment contribution"
      : "Investment withdrawal";
  }

  return transaction.type;
}

function initials(name = "User") {
  return name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function App() {
  const [token, setToken] = useState(
    () => localStorage.getItem(api.TOKEN_KEY)
  );
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({
    name: "",
    email: "",
    password: ""
  });
  const [data, setData] = useState(emptyData);
  const [filters, setFilters] = useState({
    start_date: "",
    end_date: ""
  });
  const [filterDraft, setFilterDraft] = useState({
    start_date: "",
    end_date: ""
  });
  const [transactionForm, setTransactionForm] = useState(blankTransaction());
  const [categoryName, setCategoryName] = useState("");
  const [budgetForm, setBudgetForm] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    amount: ""
  });
  const [activeSection, setActiveSection] = useState("overview");
  const [showTransactionForm, setShowTransactionForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [error, setError] = useState("");

  function showError(reason) {
    if (reason.status === 401) {
      localStorage.removeItem(api.TOKEN_KEY);
      setToken(null);
      setUser(null);
      setData(emptyData);
      setError("Your session expired. Please log in again.");
      return;
    }

    setError(reason.message || "Something went wrong.");
  }

  function signOut() {
    localStorage.removeItem(api.TOKEN_KEY);
    setToken(null);
    setUser(null);
    setData(emptyData);
    setError("");
  }

  useEffect(() => {
    if (!token) {
      return undefined;
    }

    let cancelled = false;
    setLoading(true);
    setError("");

    const query = {
      start_date: filters.start_date,
      end_date: filters.end_date
    };

    Promise.all([
      api.getCurrentUser(),
      api.getCategories(),
      api.getTransactions(query),
      api.getSummary(query),
      api.getCategoryTotals(query),
      api.getBudgets()
    ])
      .then(([currentUser, categories, transactions, summary, categoryTotals, budgets]) => {
        if (cancelled) {
          return;
        }

        setUser(currentUser);
        setData({
          summary,
          categories,
          transactions,
          budgets,
          categoryTotals
        });
        setTransactionForm((current) => (
          current.category_id || !categories.length
            ? current
            : { ...current, category_id: String(categories[0].id) }
        ));
      })
      .catch((reason) => {
        if (!cancelled) {
          showError(reason);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token, filters.start_date, filters.end_date, refreshKey]);

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setAuthLoading(true);
    setError("");

    try {
      if (authMode === "register") {
        await api.register({
          name: authForm.name.trim(),
          email: authForm.email.trim(),
          password: authForm.password
        });
      }

      const result = await api.login(
        authForm.email.trim(),
        authForm.password
      );

      localStorage.setItem(api.TOKEN_KEY, result.access_token);
      setToken(result.access_token);
    } catch (reason) {
      setError(reason.message || "Unable to authenticate.");
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleTransactionSubmit(event) {
    event.preventDefault();

    if (!transactionForm.category_id) {
      setError("Create a category before adding a transaction.");
      return;
    }

    setActionLoading("transaction");
    setError("");

    try {
      await api.createTransaction({
        category_id: Number(transactionForm.category_id),
        amount: Number(transactionForm.amount),
        type: transactionForm.type,
        debt_direction: transactionForm.type === "debt"
          ? transactionForm.debt_direction
          : null,
        interest_amount: transactionForm.type === "debt" &&
          transactionForm.interest_amount !== ""
          ? Number(transactionForm.interest_amount)
          : null,
        investment_action: transactionForm.type === "investment"
          ? transactionForm.investment_action
          : null,
        description: transactionForm.description.trim() || null,
        date: transactionForm.date
      });

      setTransactionForm(blankTransaction(transactionForm.category_id));
      setShowTransactionForm(false);
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  async function handleCategorySubmit(event) {
    event.preventDefault();
    const name = categoryName.trim();

    if (!name) {
      return;
    }

    setActionLoading("category");
    setError("");

    try {
      const category = await api.createCategory(name);
      setCategoryName("");
      setTransactionForm((current) => (
        current.category_id
          ? current
          : { ...current, category_id: String(category.id) }
      ));
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  async function handleBudgetSubmit(event) {
    event.preventDefault();
    setActionLoading("budget");
    setError("");

    try {
      await api.createBudget({
        year: Number(budgetForm.year),
        month: Number(budgetForm.month),
        amount: Number(budgetForm.amount)
      });

      setBudgetForm((current) => ({ ...current, amount: "" }));
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  async function removeTransaction(transactionId) {
    if (!window.confirm("Delete this transaction?")) {
      return;
    }

    setActionLoading("delete-" + transactionId);
    setError("");

    try {
      await api.deleteTransaction(transactionId);
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  async function removeCategory(categoryId) {
    if (!window.confirm("Delete this category?")) {
      return;
    }

    setActionLoading("category-" + categoryId);
    setError("");

    try {
      await api.deleteCategory(categoryId);
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  async function removeBudget(budgetId) {
    if (!window.confirm("Delete this budget?")) {
      return;
    }

    setActionLoading("budget-" + budgetId);
    setError("");

    try {
      await api.deleteBudget(budgetId);
      setRefreshKey((value) => value + 1);
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  function goTo(section) {
    setActiveSection(section);
    document.getElementById(section)?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  }

  function applyDateFilters(nextFilters = filterDraft) {
    if (
      nextFilters.start_date &&
      nextFilters.end_date &&
      nextFilters.start_date > nextFilters.end_date
    ) {
      setError("The start date must be before the end date.");
      return;
    }

    setError("");
    setFilters(nextFilters);
  }

  function applyDatePreset(preset) {
    const today = new Date();
    const start = new Date(today);

    if (preset === "month") {
      start.setDate(1);
    } else {
      start.setDate(today.getDate() - 29);
    }

    const nextFilters = {
      start_date: localDate(start),
      end_date: localDate(today)
    };

    setFilterDraft(nextFilters);
    applyDateFilters(nextFilters);
  }

  if (!token) {
    return (
      <AuthScreen
        mode={authMode}
        form={authForm}
        error={error}
        loading={authLoading}
        onModeChange={(mode) => {
          setAuthMode(mode);
          setError("");
        }}
        onChange={(event) => {
          setAuthForm({
            ...authForm,
            [event.target.name]: event.target.value
          });
        }}
        onSubmit={handleAuthSubmit}
      />
    );
  }

  const categoryNames = Object.fromEntries(
    data.categories.map((category) => [category.id, category.name])
  );
  const maximumCategoryTotal = Math.max(
    ...data.categoryTotals.map((item) => Number(item.total)),
    1
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">L</span>
          <span>
            <strong>Ledgerly</strong>
            <small>Expense workspace</small>
          </span>
        </div>

        <nav className="side-nav" aria-label="Main navigation">
          <button
            className={activeSection === "overview" ? "active" : ""}
            onClick={() => goTo("overview")}
          >
            <span>Overview</span>
            <span className="nav-count">01</span>
          </button>
          <button
            className={activeSection === "transactions" ? "active" : ""}
            onClick={() => goTo("transactions")}
          >
            <span>Transactions</span>
            <span className="nav-count">02</span>
          </button>
          <button
            className={activeSection === "categories" ? "active" : ""}
            onClick={() => goTo("categories")}
          >
            <span>Categories</span>
            <span className="nav-count">03</span>
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="live-dot" />
            API connected
            <small>Local development mode</small>
          </div>
          <button className="logout-button" onClick={signOut}>
            Log out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">PERSONAL FINANCE</p>
            <h1>Good to see you, {user?.name?.split(" ")[0] || "there"}.</h1>
          </div>
          <div className="topbar-actions">
            <button
              className="button button-ghost"
              onClick={() => setRefreshKey((value) => value + 1)}
              disabled={loading}
            >
              {loading ? "Refreshing..." : "Refresh"}
            </button>
            <button
              className="button button-primary"
              onClick={() => setShowTransactionForm(true)}
            >
              <span className="button-plus">+</span> Add transaction
            </button>
            <div className="avatar" title={user?.email}>
              {initials(user?.name)}
            </div>
          </div>
        </header>

        {error && (
          <div className="alert alert-error" role="alert">
            <span>{error}</span>
            <button onClick={() => setError("")} aria-label="Dismiss error">x</button>
          </div>
        )}

        <section className="filter-card">
          <div>
            <p className="eyebrow">DATE RANGE</p>
            <strong>Review your activity</strong>
          </div>
          <div className="filter-fields">
            <label>
              From
              <input
                type="date"
                value={filterDraft.start_date}
                onChange={(event) => setFilterDraft({
                  ...filterDraft,
                  start_date: event.target.value
                })}
              />
            </label>
            <span className="date-divider">to</span>
            <label>
              Until
              <input
                type="date"
                value={filterDraft.end_date}
                onChange={(event) => setFilterDraft({
                  ...filterDraft,
                  end_date: event.target.value
                })}
              />
            </label>
            <button
              className="button button-small button-ghost"
              onClick={() => applyDatePreset("month")}
            >
              This month
            </button>
            <button
              className="button button-small button-ghost"
              onClick={() => applyDatePreset("last30")}
            >
              Last 30 days
            </button>
            <button
              className="button button-small button-dark"
              onClick={() => applyDateFilters()}
            >
              Apply
            </button>
            <button
              className="button button-small button-ghost"
              onClick={() => {
                const allTime = { start_date: "", end_date: "" };
                setFilterDraft(allTime);
                applyDateFilters(allTime);
              }}
            >
              All time
            </button>
          </div>
        </section>

        <section id="overview" className="stats-grid">
          <StatCard
            label="Current balance"
            value={formatMoney(data.summary.balance)}
            note="Income minus expenses"
            tone={data.summary.balance >= 0 ? "green" : "red"}
            symbol="="
          />
          <StatCard
            label="Total income"
            value={formatMoney(data.summary.total_income)}
            note="Money coming in"
            tone="blue"
            symbol="+"
          />
          <StatCard
            label="Total expenses"
            value={formatMoney(data.summary.total_expenses)}
            note="Money going out"
            tone="orange"
            symbol="−"
          />
          <StatCard
            label="Net debt"
            value={formatMoney(data.summary.debt_borrowed - data.summary.debt_lent)}
            note="Borrowed minus lent"
            tone="purple"
            symbol="D"
          />
          <StatCard
            label="Net invested"
            value={formatMoney(
              data.summary.investment_contributions -
              data.summary.investment_withdrawals
            )}
            note="Contributions minus withdrawals"
            tone="teal"
            symbol="I"
          />
        </section>

        <section className="content-grid">
          <article className="card category-chart">
            <CardHeading
              eyebrow="SPENDING BREAKDOWN"
              title="Where your money goes"
              action={data.categoryTotals.length ? "Expenses only" : ""}
            />
            {data.categoryTotals.length ? (
              <div className="breakdown-list">
                {data.categoryTotals.map((item) => (
                  <div className="breakdown-row" key={item.category_id}>
                    <div className="breakdown-label">
                      <span className="category-dot" />
                      <span>{item.category_name}</span>
                      <strong>{formatMoney(item.total)}</strong>
                    </div>
                    <div className="progress-track">
                      <span
                        className="progress-fill"
                        style={{
                          width: (Number(item.total) / maximumCategoryTotal) * 100 + "%"
                        }}
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

          <article className="card budget-card">
            <CardHeading
              eyebrow="MONTHLY PLANS"
              title="Budgets"
              action={data.budgets.length + " saved"}
            />
            <form className="compact-form" onSubmit={handleBudgetSubmit}>
              <div className="form-row">
                <label>
                  Year
                  <input
                    type="number"
                    min="2000"
                    max="2100"
                    value={budgetForm.year}
                    onChange={(event) => setBudgetForm({
                      ...budgetForm,
                      year: event.target.value
                    })}
                  />
                </label>
                <label>
                  Month
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={budgetForm.month}
                    onChange={(event) => setBudgetForm({
                      ...budgetForm,
                      month: event.target.value
                    })}
                  />
                </label>
                <label className="amount-field">
                  Amount
                  <input
                    type="number"
                    min="1"
                    step="0.01"
                    placeholder="10,000"
                    value={budgetForm.amount}
                    onChange={(event) => setBudgetForm({
                      ...budgetForm,
                      amount: event.target.value
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
              {data.budgets.slice(0, 3).map((budget) => {
                const spent = data.transactions
                  .filter((transaction) => {
                    const transactionDate = new Date(transaction.date);
                    return (
                      transaction.type === "expense" &&
                      transactionDate.getFullYear() === budget.year &&
                      transactionDate.getMonth() + 1 === budget.month
                    );
                  })
                  .reduce((total, transaction) => total + Number(transaction.amount), 0);
                const percentage = Math.min((spent / budget.amount) * 100, 100);

                return (
                  <div className="budget-row" key={budget.id}>
                    <div className="budget-row-top">
                      <span>{budget.year}-{String(budget.month).padStart(2, "0")}</span>
                      <strong>{formatMoney(budget.amount)}</strong>
                      <button
                        className="icon-button"
                        onClick={() => removeBudget(budget.id)}
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
                    <small>{formatMoney(spent)} spent</small>
                  </div>
                );
              })}
              {!data.budgets.length && (
                <p className="muted-copy">No budgets yet. Add your first monthly plan above.</p>
              )}
            </div>
          </article>
        </section>

        <section id="transactions" className="card section-card">
          <CardHeading
            eyebrow="ACTIVITY"
            title="Recent transactions"
            action={data.transactions.length + " shown"}
          />
          {data.transactions.length ? (
            <div className="transaction-list">
              <div className="transaction-header">
                <span>Transaction</span>
                <span>Category</span>
                <span>Date</span>
                <span className="align-right">Amount</span>
                <span />
              </div>
              {data.transactions.map((transaction) => (
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
                    {transactionSign(transaction)}
                    {formatMoney(transaction.amount)}
                  </strong>
                  <button
                    className="icon-button"
                    onClick={() => removeTransaction(transaction.id)}
                    disabled={actionLoading === "delete-" + transaction.id}
                    aria-label="Delete transaction"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="Your activity will appear here"
              copy="Add your first income or expense to start your ledger."
              action={
                <button
                  className="button button-primary"
                  onClick={() => setShowTransactionForm(true)}
                >
                  Add first transaction
                </button>
              }
            />
          )}
        </section>

        <section id="categories" className="card section-card">
          <CardHeading
            eyebrow="ORGANIZE"
            title="Categories"
            action={data.categories.length + " total"}
          />
          <form className="category-form" onSubmit={handleCategorySubmit}>
            <input
              type="text"
              placeholder="Create a category, e.g. Travel"
              value={categoryName}
              maxLength="100"
              onChange={(event) => setCategoryName(event.target.value)}
            />
            <button
              className="button button-dark"
              disabled={actionLoading === "category"}
            >
              {actionLoading === "category" ? "Adding..." : "Add category"}
            </button>
          </form>
          <div className="category-grid">
            {data.categories.map((category) => (
              <div className="category-chip" key={category.id}>
                <span className="category-dot" />
                <span>{category.name}</span>
                <button
                  className="chip-delete"
                  onClick={() => removeCategory(category.id)}
                  disabled={actionLoading === "category-" + category.id}
                  aria-label={"Delete " + category.name}
                >
                  ×
                </button>
              </div>
            ))}
            {!data.categories.length && (
              <p className="muted-copy">Add a category before creating transactions.</p>
            )}
          </div>
        </section>

        <footer className="page-footer">
          <span>Ledgerly</span>
          <span>Powered by FastAPI and PostgreSQL</span>
          <span>Local development mode</span>
        </footer>
      </main>

      {showTransactionForm && (
        <div
          className="modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setShowTransactionForm(false);
            }
          }}
        >
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="transaction-title">
            <div className="modal-heading">
              <div>
                <p className="eyebrow">NEW ENTRY</p>
                <h2 id="transaction-title">Add transaction</h2>
              </div>
              <button
                className="icon-button close-button"
                onClick={() => setShowTransactionForm(false)}
                aria-label="Close transaction form"
              >
                ×
              </button>
            </div>
            {data.categories.length ? (
              <form className="modal-form" onSubmit={handleTransactionSubmit}>
                <div className="type-toggle">
                  <button
                    type="button"
                    className={transactionForm.type === "expense" ? "selected expense" : ""}
                    onClick={() => setTransactionForm({
                      ...transactionForm,
                      type: "expense"
                    })}
                  >
                    Expense
                  </button>
                  <button
                    type="button"
                    className={transactionForm.type === "income" ? "selected income" : ""}
                    onClick={() => setTransactionForm({
                      ...transactionForm,
                      type: "income"
                    })}
                  >
                    Income
                  </button>
                  <button
                    type="button"
                    className={transactionForm.type === "debt" ? "selected debt" : ""}
                    onClick={() => setTransactionForm({
                      ...transactionForm,
                      type: "debt"
                    })}
                  >
                    Debt
                  </button>
                  <button
                    type="button"
                    className={transactionForm.type === "investment" ? "selected investment" : ""}
                    onClick={() => setTransactionForm({
                      ...transactionForm,
                      type: "investment"
                    })}
                  >
                    Investment
                  </button>
                </div>
                <label>
                  Amount
                  <div className="input-prefix">
                    <span>₹</span>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      placeholder="0.00"
                      value={transactionForm.amount}
                      onChange={(event) => setTransactionForm({
                        ...transactionForm,
                        amount: event.target.value
                      })}
                      required
                    />
                  </div>
                </label>
                {transactionForm.type === "debt" && (
                  <div className="detail-panel debt-panel">
                    <label>
                      Debt direction
                      <select
                        value={transactionForm.debt_direction}
                        onChange={(event) => setTransactionForm({
                          ...transactionForm,
                          debt_direction: event.target.value
                        })}
                      >
                        <option value="borrowed">Borrowed money</option>
                        <option value="lent">Money lent out</option>
                      </select>
                    </label>
                    <label>
                      Interest amount
                      <div className="input-prefix">
                        <span>Rs</span>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          placeholder="Optional"
                          value={transactionForm.interest_amount}
                          onChange={(event) => setTransactionForm({
                            ...transactionForm,
                            interest_amount: event.target.value
                          })}
                        />
                      </div>
                    </label>
                  </div>
                )}
                {transactionForm.type === "investment" && (
                  <div className="detail-panel investment-panel">
                    <label>
                      Investment action
                      <select
                        value={transactionForm.investment_action}
                        onChange={(event) => setTransactionForm({
                          ...transactionForm,
                          investment_action: event.target.value
                        })}
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
                    value={transactionForm.category_id}
                    onChange={(event) => setTransactionForm({
                      ...transactionForm,
                      category_id: event.target.value
                    })}
                    required
                  >
                    <option value="">Select a category</option>
                    {data.categories.map((category) => (
                      <option value={category.id} key={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Description
                  <input
                    type="text"
                    maxLength="255"
                    placeholder="What was this for?"
                    value={transactionForm.description}
                    onChange={(event) => setTransactionForm({
                      ...transactionForm,
                      description: event.target.value
                    })}
                  />
                </label>
                <label>
                  Date and time
                  <input
                    type="datetime-local"
                    value={transactionForm.date}
                    onChange={(event) => setTransactionForm({
                      ...transactionForm,
                      date: event.target.value
                    })}
                    required
                  />
                </label>
                <button
                  className="button button-primary button-full"
                  disabled={actionLoading === "transaction"}
                >
                  {actionLoading === "transaction" ? "Adding..." : "Add transaction"}
                </button>
              </form>
            ) : (
              <EmptyState
                title="Create a category first"
                copy="Transactions need a category so your spending stays organized."
                action={
                  <button
                    className="button button-dark"
                    onClick={() => {
                      setShowTransactionForm(false);
                      goTo("categories");
                    }}
                  >
                    Go to categories
                  </button>
                }
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function AuthScreen({ mode, form, error, loading, onModeChange, onChange, onSubmit }) {
  const isRegister = mode === "register";

  return (
    <main className="auth-page">
      <section className="auth-showcase">
        <div className="showcase-brand">
          <span className="brand-mark">L</span>
          <strong>Ledgerly</strong>
        </div>
        <div className="showcase-copy">
          <p className="eyebrow">A CLEARER MONEY ROUTINE</p>
          <h1>Give every rupee a place to go.</h1>
          <p>
            A calm workspace for the small decisions that make your bigger
            financial picture easier to understand.
          </p>
        </div>
        <div className="showcase-metrics">
          <div>
            <strong>01</strong>
            <span>Track every entry</span>
          </div>
          <div>
            <strong>02</strong>
            <span>Plan each month</span>
          </div>
          <div>
            <strong>03</strong>
            <span>See the pattern</span>
          </div>
        </div>
        <div className="showcase-orbit orbit-one" />
        <div className="showcase-orbit orbit-two" />
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <p className="eyebrow">{isRegister ? "GET STARTED" : "WELCOME BACK"}</p>
          <h2>{isRegister ? "Create your workspace" : "Sign in to Ledgerly"}</h2>
          <p className="auth-subtitle">
            {isRegister
              ? "Start with a simple, private view of your money."
              : "Your financial overview is waiting for you."}
          </p>

          {error && <div className="alert alert-error" role="alert">{error}</div>}

          <form className="auth-form" onSubmit={onSubmit}>
            {isRegister && (
              <label>
                Your name
                <input
                  name="name"
                  type="text"
                  placeholder="Sapna"
                  value={form.name}
                  onChange={onChange}
                  minLength="1"
                  maxLength="100"
                  required
                />
              </label>
            )}
            <label>
              Email address
              <input
                name="email"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={onChange}
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                placeholder="At least 8 characters"
                value={form.password}
                onChange={onChange}
                minLength="8"
                maxLength="128"
                required
              />
            </label>
            <button className="button button-primary button-full" disabled={loading}>
              {loading
                ? "Please wait..."
                : isRegister
                  ? "Create account"
                  : "Sign in"}
            </button>
          </form>

          <p className="auth-switch">
            {isRegister ? "Already have an account?" : "New to Ledgerly?"}
            <button
              onClick={() => onModeChange(isRegister ? "login" : "register")}
            >
              {isRegister ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>
      </section>
    </main>
  );
}

function CardHeading({ eyebrow, title, action }) {
  return (
    <div className="card-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {action && <span className="card-action">{action}</span>}
    </div>
  );
}

function StatCard({ label, value, note, tone, symbol }) {
  return (
    <article className={"stat-card " + tone}>
      <div className="stat-top">
        <span className="eyebrow">{label}</span>
        <span className="stat-symbol">{symbol}</span>
      </div>
      <strong className="stat-value">{value}</strong>
      <span className="stat-note">{note}</span>
    </article>
  );
}

function EmptyState({ title, copy, action }) {
  return (
    <div className="empty-state">
      <div className="empty-mark">○</div>
      <h3>{title}</h3>
      <p>{copy}</p>
      {action}
    </div>
  );
}

export default App;
