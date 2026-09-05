from decimal import Decimal
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Budget, Category, Transaction, User
from ..schemas import AnalyticsSummaryResponse, CategoryTotalResponse
from ..security import get_current_user


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

ZERO = Decimal("0")
CENT = Decimal("0.01")


def decimal_value(value):
    amount = value if isinstance(value, Decimal) else Decimal(str(value or 0))
    # SQLite aggregates can be floats; always return an exact two-decimal value.
    return amount.quantize(CENT)


def date_filters(start_date: date | None, end_date: date | None):
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before or equal to end_date"
            )

    filters = []

    if start_date is not None:
        filters.append(
            Transaction.date >= datetime.combine(start_date, time.min)
        )

    if end_date is not None:
        next_day = end_date + timedelta(days=1)
        filters.append(
            Transaction.date < datetime.combine(next_day, time.min)
        )

    return filters


def monthly_expense_totals(db: Session, filters):
    # Get all monthly totals in one query instead of querying once per budget.
    rows = db.query(
        func.extract("year", Transaction.date).label("year"),
        func.extract("month", Transaction.date).label("month"),
        func.sum(Transaction.amount).label("total")
    ).filter(
        *filters,
        Transaction.type == "expense"
    ).group_by(
        func.extract("year", Transaction.date),
        func.extract("month", Transaction.date)
    ).all()

    return {
        (int(year), int(month)): decimal_value(total)
        for year, month, total in rows
    }


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get income, expenses, and balance"
)
def get_summary(
    start_date: date | None = Query(
        default=None,
        description="Optional first date to include."
    ),
    end_date: date | None = Query(
        default=None,
        description="Optional last date to include."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filters = [
        Transaction.user_id == current_user.id,
        *date_filters(start_date, end_date)
    ]

    totals = db.query(
        func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "income", Transaction.amount),
                    else_=0
                )
            ),
            0
        ).label("total_income"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "expense", Transaction.amount),
                    else_=0
                )
            ),
            0
        ).label("total_expenses")
    ).filter(*filters).first()

    total_income = decimal_value(totals.total_income)
    total_expenses = decimal_value(totals.total_expenses)

    detail_totals = db.query(
        func.coalesce(
            func.sum(
                case(
                    (
                        (Transaction.type == "debt")
                        & (Transaction.debt_direction == "borrowed"),
                        Transaction.amount
                    ),
                    else_=0
                )
            ),
            0
        ).label("debt_borrowed"),
        func.coalesce(
            func.sum(
                case(
                    (
                        (Transaction.type == "debt")
                        & (Transaction.debt_direction == "lent"),
                        Transaction.amount
                    ),
                    else_=0
                )
            ),
            0
        ).label("debt_lent"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "debt", Transaction.interest_amount),
                    else_=0
                )
            ),
            0
        ).label("debt_interest"),
        func.coalesce(
            func.sum(
                case(
                    (
                        (Transaction.type == "investment")
                        & (Transaction.investment_action == "contribution"),
                        Transaction.amount
                    ),
                    else_=0
                )
            ),
            0
        ).label("investment_contributions"),
        func.coalesce(
            func.sum(
                case(
                    (
                        (Transaction.type == "investment")
                        & (Transaction.investment_action == "withdrawal"),
                        Transaction.amount
                    ),
                    else_=0
                )
            ),
            0
        ).label("investment_withdrawals")
    ).filter(*filters).first()

    debt_borrowed = decimal_value(detail_totals.debt_borrowed)
    debt_lent = decimal_value(detail_totals.debt_lent)
    debt_interest = decimal_value(detail_totals.debt_interest)
    investment_contributions = decimal_value(detail_totals.investment_contributions)
    investment_withdrawals = decimal_value(detail_totals.investment_withdrawals)

    budget_query = db.query(Budget).filter(
        Budget.user_id == current_user.id
    )

    if start_date is not None:
        budget_query = budget_query.filter(
            or_(
                Budget.year > start_date.year,
                and_(
                    Budget.year == start_date.year,
                    Budget.month >= start_date.month
                )
            )
        )

    if end_date is not None:
        budget_query = budget_query.filter(
            or_(
                Budget.year < end_date.year,
                and_(
                    Budget.year == end_date.year,
                    Budget.month <= end_date.month
                )
            )
        )

    budgets = budget_query.all()
    budget_total = sum(
        (decimal_value(budget.amount) for budget in budgets),
        ZERO
    )
    monthly_expenses = monthly_expense_totals(db, filters) if budgets else {}
    budget_spent = ZERO
    budget_remaining = ZERO
    unspent_budget = ZERO

    for budget in budgets:
        spent = monthly_expenses.get((budget.year, budget.month), ZERO)
        remaining = decimal_value(budget.amount) - spent
        budget_spent += spent
        budget_remaining += remaining
        # An overspent budget must not artificially increase available cash.
        unspent_budget += max(remaining, ZERO)

    # Keep budget planning separate from cash, then include debt and investment cash flow.
    cash_balance = (
        total_income - total_expenses
        + debt_borrowed - debt_lent
        - investment_contributions + investment_withdrawals
    )

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
        "cash_balance": cash_balance,
        "budget_total": budget_total,
        "budget_spent": budget_spent,
        "budget_remaining": budget_remaining,
        "available_after_budgets": cash_balance - unspent_budget,
        "debt_borrowed": debt_borrowed,
        "debt_lent": debt_lent,
        "debt_interest": debt_interest,
        "investment_contributions": investment_contributions,
        "investment_withdrawals": investment_withdrawals
    }


@router.get(
    "/by-category",
    response_model=list[CategoryTotalResponse],
    summary="Get expenses grouped by category"
)
def get_totals_by_category(
    start_date: date | None = Query(
        default=None,
        description="Optional first date to include."
    ),
    end_date: date | None = Query(
        default=None,
        description="Optional last date to include."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filters = [
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Category.user_id == current_user.id,
        *date_filters(start_date, end_date)
    ]

    totals = db.query(
        Category.id.label("category_id"),
        Category.name.label("category_name"),
        func.sum(Transaction.amount).label("total")
    ).join(
        Category,
        Category.id == Transaction.category_id
    ).filter(
        *filters
    ).group_by(
        Category.id,
        Category.name
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).all()

    return [
        {
            "category_id": category_id,
            "category_name": category_name,
            "total": decimal_value(total)
        }
        for category_id, category_name, total in totals
    ]
