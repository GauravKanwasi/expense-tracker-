from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..finance import (
    ZERO,
    is_complete_budget_month,
    money_difference,
    money_sum,
    month_bounds,
    month_key,
    range_contains_complete_month,
    user_zone,
    utc_day_bounds,
)
from ..model import Budget, Category, Transaction, User
from ..schemas import AnalyticsSummaryResponse, CategoryTotalResponse
from ..security import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


def date_filters(start_date: date | None, end_date: date | None, timezone_name: str):
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )
    start, end = utc_day_bounds(start_date, end_date, user_zone(timezone_name))
    filters = []
    if start is not None:
        filters.append(Transaction.date >= start)
    if end is not None:
        filters.append(Transaction.date < end)
    return filters


def full_month_budgets(budgets, start_date, end_date):
    if start_date is None and end_date is None:
        return budgets, "all_time"
    selected = [
        budget
        for budget in budgets
        if is_complete_budget_month(budget.year, budget.month, start_date, end_date)
    ]
    scope = (
        "complete_months"
        if range_contains_complete_month(start_date, end_date)
        else "partial_range"
    )
    return selected, scope


def monthly_expense_totals(db: Session, budgets, timezone_name: str):
    if not budgets:
        return {}

    zone = user_zone(timezone_name)
    bounds = [month_bounds(budget.year, budget.month, zone) for budget in budgets]
    expected_months = {(budget.year, budget.month) for budget in budgets}
    rows = (
        db.query(Transaction.date, Transaction.amount)
        .filter(
            Transaction.user_id == budgets[0].user_id,
            Transaction.type == "expense",
            Transaction.date >= min(start for start, _ in bounds),
            Transaction.date < max(end for _, end in bounds),
        )
        .all()
    )
    totals = {key: ZERO for key in expected_months}
    for occurred_at, amount in rows:
        key = month_key(occurred_at, zone)
        if key in totals:
            totals[key] = money_sum((totals[key], amount))
    return totals


@router.get(
    "/summary", response_model=AnalyticsSummaryResponse, summary="Get income, expenses, and balance"
)
def get_summary(
    start_date: date | None = Query(default=None, description="Optional first date to include."),
    end_date: date | None = Query(default=None, description="Optional last date to include."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = [
        Transaction.user_id == current_user.id,
        *date_filters(start_date, end_date, current_user.timezone),
    ]
    transactions = db.query(Transaction).filter(*filters).all()

    def total(type_name: str):
        return money_sum(
            transaction.amount for transaction in transactions if transaction.type == type_name
        )

    total_income = total("income")
    total_expenses = total("expense")
    debt_borrowed = money_sum(
        transaction.amount
        for transaction in transactions
        if transaction.type == "debt" and transaction.debt_direction == "borrowed"
    )
    debt_lent = money_sum(
        transaction.amount
        for transaction in transactions
        if transaction.type == "debt" and transaction.debt_direction == "lent"
    )
    debt_interest = money_sum(
        transaction.interest_amount for transaction in transactions if transaction.type == "debt"
    )
    investment_contributions = money_sum(
        transaction.amount
        for transaction in transactions
        if transaction.type == "investment" and transaction.investment_action == "contribution"
    )
    investment_withdrawals = money_sum(
        transaction.amount
        for transaction in transactions
        if transaction.type == "investment" and transaction.investment_action == "withdrawal"
    )

    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    budgets, budget_scope = full_month_budgets(budgets, start_date, end_date)
    monthly_expenses = monthly_expense_totals(db, budgets, current_user.timezone)
    budget_total = money_sum(budget.amount for budget in budgets)
    budget_spent = ZERO
    budget_remaining = ZERO
    unspent_budget = ZERO

    for budget in budgets:
        spent = monthly_expenses.get((budget.year, budget.month), ZERO)
        remaining = money_difference(budget.amount, spent)
        budget_spent = money_sum((budget_spent, spent))
        budget_remaining = money_sum((budget_remaining, remaining))
        # An overspent budget must not artificially increase available cash.
        unspent_budget = money_sum((unspent_budget, max(remaining, ZERO)))

    # Keep budget planning separate from cash, then include debt and investment cash flow.
    cash_balance = money_difference(
        money_sum((total_income, debt_borrowed, investment_withdrawals)),
        money_sum((total_expenses, debt_lent, investment_contributions)),
    )

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": money_difference(total_income, total_expenses),
        "cash_balance": cash_balance,
        "budget_total": budget_total,
        "budget_spent": budget_spent,
        "budget_remaining": budget_remaining,
        "available_after_budgets": money_difference(cash_balance, unspent_budget),
        "debt_borrowed": debt_borrowed,
        "debt_lent": debt_lent,
        "debt_interest": debt_interest,
        "investment_contributions": investment_contributions,
        "investment_withdrawals": investment_withdrawals,
        "budget_scope": budget_scope,
    }


@router.get(
    "/by-category",
    response_model=list[CategoryTotalResponse],
    summary="Get expenses grouped by category",
)
def get_totals_by_category(
    start_date: date | None = Query(default=None, description="Optional first date to include."),
    end_date: date | None = Query(default=None, description="Optional last date to include."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = [
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Category.user_id == current_user.id,
        *date_filters(start_date, end_date, current_user.timezone),
    ]

    rows = (
        db.query(Category.id, Category.name, Transaction.amount)
        .join(Transaction, Category.id == Transaction.category_id)
        .filter(*filters)
        .all()
    )
    totals = {}
    for category_id, category_name, amount in rows:
        existing_name, existing_total = totals.get(category_id, (category_name, ZERO))
        totals[category_id] = existing_name, money_sum((existing_total, amount))
    return [
        {"category_id": category_id, "category_name": name, "total": total}
        for category_id, (name, total) in sorted(
            totals.items(), key=lambda item: item[1][1], reverse=True
        )
    ]
