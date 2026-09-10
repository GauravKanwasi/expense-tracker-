import { useEffect, useRef, useState } from "react";
import { AnimatePresence, LazyMotion, MotionConfig } from "motion/react";
import * as api from "./api";
import AnalyticsPanel from "./components/AnalyticsPanel";
import AuthScreen from "./components/AuthScreen";
import BudgetsPanel from "./components/BudgetsPanel";
import CategoriesPanel from "./components/CategoriesPanel";
import RecurringPanel from "./components/RecurringPanel";
import TransactionModal from "./components/TransactionModal";
import TransactionsPanel from "./components/TransactionsPanel";
import {
  blankTransaction,
  blankRecurring,
  emptyData,
  initials,
  isValidMoneyInput,
  localDate,
  localDateTime,
  STAT_IDS,
  STAT_ORDER_KEY,
  TRANSACTIONS_PER_PAGE
} from "./utils";
import "./styles.css";

const loadMotionFeatures = () => import("./motionFeatures").then((module) => module.default);

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(api.TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ name: "", email: "", password: "" });
  const [data, setData] = useState(emptyData);
  const [filters, setFilters] = useState({
    start_date: "", end_date: "", type: "", category_id: ""
  });
  const [filterDraft, setFilterDraft] = useState({ start_date: "", end_date: "" });
  const [transactionForm, setTransactionForm] = useState(blankTransaction());
  const [recurringForm, setRecurringForm] = useState(blankRecurring());
  const [categoryName, setCategoryName] = useState("");
  const [budgetForm, setBudgetForm] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    amount: ""
  });
  const [activeSection, setActiveSection] = useState("overview");
  const [showTransactionForm, setShowTransactionForm] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editingBudget, setEditingBudget] = useState(null);
  const [transactionError, setTransactionError] = useState("");
  const [transactionPage, setTransactionPage] = useState(0);
  const [statOrder, setStatOrder] = useState(loadStatOrder);
  const [draggedStat, setDraggedStat] = useState("");
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [error, setError] = useState("");
  const lastFocusedElement = useRef(null);

  useEffect(() => {
    localStorage.setItem(STAT_ORDER_KEY, JSON.stringify(statOrder));
  }, [statOrder]);

  useEffect(() => {
    if (!token) return undefined;

    let cancelled = false;
    const query = {
      start_date: filters.start_date,
      end_date: filters.end_date,
      type: filters.type,
      category_id: filters.category_id,
      skip: transactionPage * TRANSACTIONS_PER_PAGE,
      limit: TRANSACTIONS_PER_PAGE
    };
    const update = (changes) => !cancelled && setData((current) => ({ ...current, ...changes }));

    setLoading(true);
    setError("");
    Promise.all([
      api.getCurrentUser(),
      api.getCategories(),
      api.getTransactions(query),
      api.getSummary(query),
      api.getCategoryTotals(query),
      api.getBudgets(),
      api.getRecurringTransactions()
    ])
      .then(([currentUser, categories, transactions, summary, categoryTotals, budgets, recurring]) => {
        if (cancelled) return;
        setUser(currentUser);
        update({
          summary,
          categories,
          transactions: transactions.items,
          transactionTotal: transactions.total,
          categoryTotals,
          budgets,
          recurring
        });
        setTransactionForm((current) => current.category_id || !categories.length
          ? current
          : { ...current, category_id: String(categories[0].id) });
        setRecurringForm((current) => current.category_id || !categories.length
          ? current
          : { ...current, category_id: String(categories[0].id) });
      })
      .catch(showError)
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [
    token,
    filters.start_date,
    filters.end_date,
    filters.type,
    filters.category_id,
    refreshKey,
    transactionPage
  ]);

  function clearSession(message = "") {
    localStorage.removeItem(api.TOKEN_KEY);
    setToken(null);
    setUser(null);
    setData(emptyData);
    setError(message);
  }

  function showError(reason) {
    if (reason?.status === 401) {
      clearSession("Your session expired. Please log in again.");
      return;
    }
    setError(reason?.message || "Something went wrong.");
  }

  async function signOut() {
    try {
      await api.logout();
    } catch {
      // Local sign-out must work even when the token has already expired.
    } finally {
      clearSession();
    }
  }

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
      const result = await api.login(authForm.email.trim(), authForm.password);
      localStorage.setItem(api.TOKEN_KEY, result.access_token);
      setToken(result.access_token);
    } catch (reason) {
      setError(reason?.message || "Unable to authenticate.");
    } finally {
      setAuthLoading(false);
    }
  }

  function openTransactionModal(transaction = null) {
    lastFocusedElement.current = document.activeElement;
    setTransactionError("");
    setEditingTransaction(transaction);
    setTransactionForm(transaction ? {
      category_id: String(transaction.category_id),
      amount: String(transaction.amount),
      type: transaction.type,
      debt_direction: transaction.debt_direction || "borrowed",
      interest_amount: transaction.interest_amount || "",
      investment_action: transaction.investment_action || "contribution",
      description: transaction.description || "",
      date: localDateTime(transaction.date)
    } : blankTransaction(data.categories[0]?.id || ""));
    setShowTransactionForm(true);
  }

  function closeTransactionModal() {
    setShowTransactionForm(false);
    setEditingTransaction(null);
    setTransactionError("");
    setTimeout(() => lastFocusedElement.current?.focus(), 0);
  }

  async function handleTransactionSubmit(event) {
    event.preventDefault();
    if (!transactionForm.category_id) {
      return setTransactionError("Create a category before adding a transaction.");
    }
    if (!isValidMoneyInput(transactionForm.amount)) {
      return setTransactionError("Enter an amount greater than zero with up to 29 digits and 2 decimals.");
    }
    if (transactionForm.type === "debt" && transactionForm.interest_amount &&
      !isValidMoneyInput(transactionForm.interest_amount, true)) {
      return setTransactionError("Enter a valid interest amount or leave it empty.");
    }

    setActionLoading("transaction");
    setTransactionError("");
    setError("");
    const payload = {
      category_id: Number(transactionForm.category_id),
      amount: transactionForm.amount,
      type: transactionForm.type,
      debt_direction: transactionForm.type === "debt" ? transactionForm.debt_direction : null,
      interest_amount: transactionForm.type === "debt" && transactionForm.interest_amount
        ? transactionForm.interest_amount
        : null,
      investment_action: transactionForm.type === "investment"
        ? transactionForm.investment_action
        : null,
      description: transactionForm.description.trim() || null,
      date: transactionForm.date
    };
    try {
      if (editingTransaction) {
        await api.updateTransaction(editingTransaction.id, payload);
      } else {
        await api.createTransaction(payload);
      }
      closeTransactionModal();
      setTransactionPage(0);
      refresh();
    } catch (reason) {
      if (reason?.status === 401) {
        showError(reason);
      } else {
        setTransactionError(reason?.message || "Unable to save this transaction.");
      }
    } finally {
      setActionLoading("");
    }
  }

  function beginCategoryEdit(category) {
    setEditingCategory(category);
    setCategoryName(category.name);
  }

  function cancelCategoryEdit() {
    setEditingCategory(null);
    setCategoryName("");
  }

  async function handleCategorySubmit(event) {
    event.preventDefault();
    const name = categoryName.trim();
    if (!name) return;

    setActionLoading("category");
    setError("");
    try {
      const category = editingCategory
        ? await api.updateCategory(editingCategory.id, name)
        : await api.createCategory(name);
      setCategoryName("");
      setEditingCategory(null);
      setTransactionForm((current) => current.category_id
        ? current
        : { ...current, category_id: String(category.id) });
      refresh();
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  function beginBudgetEdit(budget) {
    setEditingBudget(budget);
    setBudgetForm({ year: budget.year, month: budget.month, amount: String(budget.amount) });
  }

  function cancelBudgetEdit() {
    setEditingBudget(null);
    setBudgetForm((current) => ({ ...current, amount: "" }));
  }

  async function handleBudgetSubmit(event) {
    event.preventDefault();
    if (!isValidMoneyInput(budgetForm.amount)) {
      return setError("Enter a budget greater than zero with up to 29 digits and 2 decimals.");
    }

    setActionLoading("budget");
    setError("");
    try {
      const payload = {
        year: Number(budgetForm.year),
        month: Number(budgetForm.month),
        amount: budgetForm.amount
      };
      if (editingBudget) {
        await api.updateBudget(editingBudget.id, payload);
      } else {
        await api.createBudget(payload);
      }
      setEditingBudget(null);
      setBudgetForm((current) => ({ ...current, amount: "" }));
      refresh();
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  function recurringPayload(source, active = source.active) {
    return {
      category_id: Number(source.category_id),
      amount: source.amount,
      type: source.type,
      description: source.description.trim?.() || null,
      debt_direction: source.type === "debt" ? source.debt_direction : null,
      interest_amount: source.type === "debt" && source.interest_amount
        ? source.interest_amount
        : null,
      investment_action: source.type === "investment" ? source.investment_action : null,
      frequency: source.frequency,
      next_due_at: source.next_due_at,
      active
    };
  }

  async function handleRecurringSubmit(event) {
    event.preventDefault();
    if (!recurringForm.category_id) return setError("Choose a category for this schedule.");
    if (!isValidMoneyInput(recurringForm.amount)) {
      return setError("Enter a recurring amount greater than zero with up to 29 digits and 2 decimals.");
    }
    if (recurringForm.type === "debt" && recurringForm.interest_amount &&
      !isValidMoneyInput(recurringForm.interest_amount, true)) {
      return setError("Enter a valid recurring interest amount or leave it empty.");
    }

    setActionLoading("recurring");
    setError("");
    try {
      await api.createRecurringTransaction(recurringPayload(recurringForm));
      setRecurringForm(blankRecurring(data.categories[0]?.id || ""));
      refresh();
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  async function generateRecurringEntries() {
    setActionLoading("generate-recurring");
    setError("");
    try {
      await api.generateRecurringTransactions();
      setTransactionPage(0);
      refresh();
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  async function toggleRecurring(rule) {
    setActionLoading("recurring-" + rule.id);
    setError("");
    try {
      await api.updateRecurringTransaction(rule.id, recurringPayload(rule, !rule.active));
      refresh();
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  async function removeItem(kind, id, message) {
    if (!window.confirm(message)) return;

    const loadingKey = kind + "-" + id;
    setActionLoading(loadingKey);
    setError("");
    try {
      if (kind === "delete") {
        await api.deleteTransaction(id);
        if (data.transactions.length === 1 && transactionPage > 0) {
          setTransactionPage((page) => page - 1);
        }
      } else if (kind === "category") {
        await api.deleteCategory(id);
      } else if (kind === "recurring") {
        await api.deleteRecurringTransaction(id);
      } else {
        await api.deleteBudget(id);
        setData((current) => ({
          ...current,
          budgets: current.budgets.filter((budget) => budget.id !== id)
        }));
      }
      refresh();
    } catch (reason) {
      showError(reason);
    } finally {
      setActionLoading("");
    }
  }

  function refresh() {
    setRefreshKey((value) => value + 1);
  }

  function goTo(section) {
    setActiveSection(section);
    document.getElementById(section)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function applyDateFilters(nextFilters = filterDraft) {
    if (nextFilters.start_date && nextFilters.end_date &&
      nextFilters.start_date > nextFilters.end_date) {
      return setError("The start date must be before the end date.");
    }
    setError("");
    setTransactionPage(0);
    setFilters((current) => ({ ...current, ...nextFilters }));
  }

  function updateTransactionFilters(changes) {
    setTransactionPage(0);
    setFilters((current) => ({ ...current, ...changes }));
  }

  function applyDatePreset(preset) {
    const today = new Date();
    const start = new Date(today);
    preset === "month" ? start.setDate(1) : start.setDate(today.getDate() - 29);
    const nextFilters = { start_date: localDate(start), end_date: localDate(today) };
    setFilterDraft(nextFilters);
    applyDateFilters(nextFilters);
  }

  function handleStatDragStart(event, statId) {
    setDraggedStat(statId);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", statId);
  }

  function handleStatDrop(event, targetId) {
    event.preventDefault();
    const sourceId = draggedStat || event.dataTransfer.getData("text/plain");
    if (!sourceId || sourceId === targetId) return setDraggedStat("");
    setStatOrder((order) => {
      const next = [...order];
      const sourceIndex = next.indexOf(sourceId);
      const targetIndex = next.indexOf(targetId);
      if (sourceIndex < 0 || targetIndex < 0) return order;
      const [source] = next.splice(sourceIndex, 1);
      next.splice(next.indexOf(targetId), 0, source);
      return next;
    });
    setDraggedStat("");
  }

  if (!token) {
    return <AuthScreen
      mode={authMode}
      form={authForm}
      error={error}
      loading={authLoading}
      onModeChange={(mode) => { setAuthMode(mode); setError(""); }}
      onChange={(event) => setAuthForm({ ...authForm, [event.target.name]: event.target.value })}
      onSubmit={handleAuthSubmit}
    />;
  }

  return (
    <LazyMotion features={loadMotionFeatures}>
      <MotionConfig reducedMotion="user">
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">L</span>
          <span><strong>Ledgerly</strong><small>Expense workspace</small></span>
        </div>
        <nav className="side-nav" aria-label="Main navigation">
          {[
            ["overview", "Overview", "01"],
            ["transactions", "Transactions", "02"],
            ["categories", "Categories", "03"],
            ["recurring", "Schedules", "04"]
          ].map(([section, label, count]) => (
            <button
              key={section}
              className={activeSection === section ? "active" : ""}
              onClick={() => goTo(section)}
            >
              <span>{label}</span><span className="nav-count">{count}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note"><span className="live-dot" />API connected<small>Local development mode</small></div>
          <button className="logout-button" onClick={signOut}>Log out</button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">PERSONAL FINANCE</p>
            <h1>Good to see you, {user?.name?.split(" ")[0] || "there"}.</h1>
          </div>
          <div className="topbar-actions">
            <button className="button button-ghost" onClick={refresh} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh"}
            </button>
            <button className="button button-primary button-glow" onClick={() => openTransactionModal()}>
              <span className="button-plus">+</span> Add transaction
            </button>
            <button className="mobile-logout" onClick={signOut}>Log out</button>
            <div className="avatar" title={user?.email}>{initials(user?.name)}</div>
          </div>
        </header>

        {error && <div className="alert alert-error" role="alert">
          <span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error">x</button>
        </div>}
        {loading && <div className="loading-indicator" role="status">Loading your workspace…</div>}

        <section className="filter-card">
          <div><p className="eyebrow">DATE RANGE</p><strong>Review your activity</strong></div>
          <div className="filter-fields">
            <label>From<input type="date" value={filterDraft.start_date} onChange={(event) => setFilterDraft({ ...filterDraft, start_date: event.target.value })} /></label>
            <span className="date-divider">to</span>
            <label>Until<input type="date" value={filterDraft.end_date} onChange={(event) => setFilterDraft({ ...filterDraft, end_date: event.target.value })} /></label>
            <button className="button button-small button-ghost" onClick={() => applyDatePreset("month")}>This month</button>
            <button className="button button-small button-ghost" onClick={() => applyDatePreset("last30")}>Last 30 days</button>
            <button className="button button-small button-dark" onClick={() => applyDateFilters()}>Apply</button>
            <button className="button button-small button-ghost" onClick={() => {
              const allTime = { start_date: "", end_date: "" };
              setFilterDraft(allTime);
              applyDateFilters(allTime);
            }}>All time</button>
          </div>
        </section>

        <AnalyticsPanel
          summary={data.summary}
          categoryTotals={data.categoryTotals}
          statOrder={statOrder}
          draggedStat={draggedStat}
          onDragStart={handleStatDragStart}
          onDragOver={(event) => { event.preventDefault(); event.dataTransfer.dropEffect = "move"; }}
          onDrop={handleStatDrop}
          onDragEnd={() => setDraggedStat("")}
        >
          <BudgetsPanel
            budgets={data.budgets}
            form={budgetForm}
            editing={editingBudget}
            onFormChange={setBudgetForm}
            actionLoading={actionLoading}
            onSubmit={handleBudgetSubmit}
            onDelete={(id) => removeItem("budget", id, "Delete this budget?")}
            onEdit={beginBudgetEdit}
            onCancelEdit={cancelBudgetEdit}
          />
        </AnalyticsPanel>

        <RecurringPanel
          recurring={data.recurring}
          categories={data.categories}
          form={recurringForm}
          actionLoading={actionLoading}
          onFormChange={setRecurringForm}
          onSubmit={handleRecurringSubmit}
          onGenerate={generateRecurringEntries}
          onToggle={toggleRecurring}
          onDelete={(id) => removeItem("recurring", id, "Delete this recurring schedule?")}
        />

        <TransactionsPanel
          transactions={data.transactions}
          total={data.transactionTotal}
          categories={data.categories}
          page={transactionPage}
          pageSize={TRANSACTIONS_PER_PAGE}
          actionLoading={actionLoading}
          filters={filters}
          onDelete={(id) => removeItem("delete", id, "Delete this transaction?")}
          onEdit={openTransactionModal}
          onAdd={() => openTransactionModal()}
          onPageChange={setTransactionPage}
          onFiltersChange={updateTransactionFilters}
        />

        <CategoriesPanel
          categories={data.categories}
          categoryName={categoryName}
          editing={editingCategory}
          onCategoryNameChange={setCategoryName}
          actionLoading={actionLoading}
          onSubmit={handleCategorySubmit}
          onDelete={(id) => removeItem("category", id, "Delete this category?")}
          onEdit={beginCategoryEdit}
          onCancelEdit={cancelCategoryEdit}
        />

        <footer className="page-footer">
          <span>Ledgerly</span><span>Powered by FastAPI and PostgreSQL</span><span>Local development mode</span>
        </footer>
      </main>

      <AnimatePresence>
        {showTransactionForm && (
          <TransactionModal
            key="transaction-modal"
            visible
            form={transactionForm}
            categories={data.categories}
            actionLoading={actionLoading}
            editing={editingTransaction}
            error={transactionError}
            onFormChange={(form) => { setTransactionForm(form); setTransactionError(""); }}
            onSubmit={handleTransactionSubmit}
            onClose={closeTransactionModal}
            onGoToCategories={() => { closeTransactionModal(); goTo("categories"); }}
          />
        )}
      </AnimatePresence>
    </div>
      </MotionConfig>
    </LazyMotion>
  );
}

function loadStatOrder() {
  try {
    const saved = JSON.parse(localStorage.getItem(STAT_ORDER_KEY));
    return Array.isArray(saved) && saved.length === STAT_IDS.length &&
      new Set(saved).size === STAT_IDS.length &&
      saved.every((id) => STAT_IDS.includes(id)) ? saved : STAT_IDS;
  } catch {
    return STAT_IDS;
  }
}

export default App;
