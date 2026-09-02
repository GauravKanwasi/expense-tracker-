from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Category, Transaction, User
from ..schemas import AnalyticsSummaryResponse, CategoryTotalResponse
from ..security import get_current_user


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


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

    total_income = float(totals.total_income or 0)
    total_expenses = float(totals.total_expenses or 0)

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

    debt_borrowed = float(detail_totals.debt_borrowed or 0)
    debt_lent = float(detail_totals.debt_lent or 0)
    debt_interest = float(detail_totals.debt_interest or 0)
    investment_contributions = float(detail_totals.investment_contributions or 0)
    investment_withdrawals = float(detail_totals.investment_withdrawals or 0)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
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
            "total": float(total)
        }
        for category_id, category_name, total in totals
    ]
