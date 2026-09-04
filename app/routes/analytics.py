from decimal import Decimal
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Budget, Category, Transaction, User
from ..schemas import AnalyticsSummaryResponse, CategoryTotalResponse
from ..security import get_current_user
from .budgets import month_bounds


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

ZERO = Decimal("0")


def decimal_value(value):
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


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
    budget_month_filters = []

    for budget in budgets:
        month_start, month_end = month_bounds(budget.year, budget.month)
        budget_month_filters.append(
            and_(
                Transaction.date >= month_start,
                Transaction.date < month_end
            )
        )

    if budget_month_filters:
        budget_spent = db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            *filters,
            Transaction.type == "expense",
            or_(*budget_month_filters)
        ).scalar()
        budget_spent = decimal_value(budget_spent)
    else:
        budget_spent = ZERO

    # Budget planning hai; ise cash balance se alag rakhkar available amount nikalo.
    budget_remaining = budget_total - budget_spent
    # Debt aur investments ko unke cash-flow direction ke hisaab se include karo.
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
        "available_after_budgets": cash_balance - budget_remaining,
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
