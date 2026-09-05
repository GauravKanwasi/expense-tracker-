from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


def register_user(client, email="user@example.com", password="Password123"):
    response = client.post(
        "/users/",
        json={
            "name": "Test User",
            "email": email,
            "password": password
        }
    )
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(client, email="user@example.com", password="Password123"):
    login = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_category(client, headers, name="Food"):
    response = client.post(
        "/categories/",
        json={"name": name},
        headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def create_transaction(
    client,
    headers,
    category_id,
    amount,
    transaction_type,
    transaction_date,
    description="Test transaction"
):
    response = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": amount,
            "type": transaction_type,
            "description": description,
            "date": transaction_date
        },
        headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_registration_duplicate_email_and_login(client):
    register_user(client)

    duplicate = client.post(
        "/users/",
        json={
            "name": "Another User",
            "email": "user@example.com",
            "password": "Password123"
        }
    )
    assert duplicate.status_code == 400

    short_password = client.post(
        "/users/",
        json={
            "name": "Short Password",
            "email": "short@example.com",
            "password": "short"
        }
    )
    assert short_password.status_code == 422

    invalid_login = client.post(
        "/auth/login",
        data={
            "username": "user@example.com",
            "password": "wrong-password"
        }
    )
    assert invalid_login.status_code == 401

    headers = auth_headers(client)
    response = client.get("/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_login_rate_limit_and_logout(client):
    register_user(client)

    for _ in range(5):
        invalid_login = client.post(
            "/auth/login",
            data={"username": "user@example.com", "password": "wrong-password"}
        )
        assert invalid_login.status_code == 401

    rate_limited = client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "wrong-password"}
    )
    assert rate_limited.status_code == 429
    assert "retry-after" in rate_limited.headers

    clear_login = client.post(
        "/auth/login",
        data={"username": "another@example.com", "password": "wrong-password"}
    )
    assert clear_login.status_code == 401


def test_logout_revokes_the_current_token(client):
    register_user(client)
    headers = auth_headers(client)

    logout = client.post("/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert logout.json() == {"message": "Logged out successfully"}

    protected_request = client.get("/users/me", headers=headers)
    assert protected_request.status_code == 401


def test_account_and_category_text_is_normalized(client):
    created_user = client.post(
        "/users/",
        json={
            "name": "  Test User  ",
            "email": "  USER@EXAMPLE.COM  ",
            "password": "Password123"
        }
    )
    assert created_user.status_code == 200, created_user.text
    assert created_user.json() == {
        "id": 1,
        "name": "Test User",
        "email": "user@example.com"
    }

    headers = auth_headers(client, email=" USER@EXAMPLE.COM ")
    category = client.post(
        "/categories/",
        json={"name": "  Food  "},
        headers=headers
    )
    assert category.status_code == 200
    assert category.json()["name"] == "Food"

    duplicate_category = client.post(
        "/categories/",
        json={"name": "food"},
        headers=headers
    )
    assert duplicate_category.status_code == 400

    blank_category = client.post(
        "/categories/",
        json={"name": "   "},
        headers=headers
    )
    assert blank_category.status_code == 422


def test_protected_routes_require_authentication(client):
    protected_routes = [
        "/users/me",
        "/categories/",
        "/transactions/",
        "/budgets/",
        "/analytics/summary"
    ]

    for route in protected_routes:
        response = client.get(route)
        assert response.status_code == 401


def test_unexpected_errors_have_a_safe_response(client):
    register_user(client)
    headers = auth_headers(client)
    original_override = app.dependency_overrides[get_db]

    def broken_database_dependency():
        raise RuntimeError("Test-only database failure")

    app.dependency_overrides[get_db] = broken_database_dependency
    try:
        with TestClient(app, raise_server_exceptions=False) as safe_client:
            response = safe_client.get("/users/me", headers=headers)
    finally:
        app.dependency_overrides[get_db] = original_override

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_cors_allows_local_frontend(client):
    response = client.options(
        "/transactions/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )


def test_cors_rejects_unknown_frontend(client):
    response = client.options(
        "/transactions/",
        headers={
            "Origin": "http://untrusted.example",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert "access-control-allow-origin" not in response.headers


def test_category_ownership(client):
    register_user(client)
    first_headers = auth_headers(client)
    category_id = create_category(client, first_headers)
    transaction = create_transaction(
        client,
        first_headers,
        category_id,
        250,
        "expense",
        "2026-08-29T12:00:00"
    )

    register_user(client, email="second@example.com")
    second_headers = auth_headers(client, email="second@example.com")

    response = client.get(
        f"/categories/{category_id}",
        headers=second_headers
    )

    assert response.status_code == 404

    transaction_response = client.get(
        f"/transactions/{transaction['id']}",
        headers=second_headers
    )
    assert transaction_response.status_code == 404

    cannot_delete = client.delete(
        f"/categories/{category_id}",
        headers=first_headers
    )
    assert cannot_delete.status_code == 400


def test_transaction_crud_filters_and_pagination(client):
    register_user(client)
    headers = auth_headers(client)
    food_id = create_category(client, headers, "Food")
    tax_id = create_category(client, headers, "Tax")

    expense = create_transaction(
        client, headers, food_id, 250, "expense", "2026-08-29T12:00:00"
    )
    income = create_transaction(
        client, headers, food_id, 1000, "income", "2026-08-28T12:00:00"
    )
    later_expense = create_transaction(
        client, headers, tax_id, 100, "expense", "2026-09-01T12:00:00"
    )

    all_transactions = client.get("/transactions/", headers=headers)
    assert all_transactions.status_code == 200
    assert [item["id"] for item in all_transactions.json()["items"]] == [
        later_expense["id"], expense["id"], income["id"]
    ]
    assert all_transactions.json()["total"] == 3

    expense_filter = client.get(
        "/transactions/?type=expense",
        headers=headers
    )
    assert len(expense_filter.json()["items"]) == 2
    assert expense_filter.json()["total"] == 2

    category_filter = client.get(
        f"/transactions/?category_id={food_id}",
        headers=headers
    )
    assert len(category_filter.json()["items"]) == 2

    date_filter = client.get(
        "/transactions/?start_date=2026-08-01&end_date=2026-08-31",
        headers=headers
    )
    assert len(date_filter.json()["items"]) == 2

    page = client.get(
        "/transactions/?skip=1&limit=1",
        headers=headers
    )
    assert [item["id"] for item in page.json()["items"]] == [expense["id"]]
    assert page.json()["total"] == 3

    updated = client.put(
        f"/transactions/{expense['id']}",
        json={
            "category_id": tax_id,
            "amount": 300,
            "type": "expense",
            "description": "Updated expense",
            "date": "2026-08-29T12:00:00"
        },
        headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == "300.00"

    deleted = client.delete(
        f"/transactions/{expense['id']}",
        headers=headers
    )
    assert deleted.status_code == 200

    missing = client.get(
        f"/transactions/{expense['id']}",
        headers=headers
    )
    assert missing.status_code == 404


def test_transaction_validation(client):
    register_user(client)
    headers = auth_headers(client)
    category_id = create_category(client, headers)

    invalid_type = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": 100,
            "type": "invalid",
            "date": "2026-08-29T12:00:00"
        },
        headers=headers
    )
    assert invalid_type.status_code == 422

    invalid_amount = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": 0,
            "type": "expense",
            "date": "2026-08-29T12:00:00"
        },
        headers=headers
    )
    assert invalid_amount.status_code == 422

    invalid_filter = client.get(
        "/transactions/?type=invalid",
        headers=headers
    )
    assert invalid_filter.status_code == 400


def test_large_money_values_are_preserved(client):
    register_user(client)
    headers = auth_headers(client)
    category_id = create_category(client, headers, "Large amounts")
    maximum_amount = "99999999999999999999999999999.99"

    response = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": maximum_amount,
            "type": "income",
            "date": "2026-08-29T12:00:00"
        },
        headers=headers
    )

    assert response.status_code == 200, response.text
    assert response.json()["amount"] == maximum_amount


def test_money_totals_keep_two_decimal_places(client):
    register_user(client)
    headers = auth_headers(client)
    category_id = create_category(client, headers, "Small values")

    budget = client.post(
        "/budgets/",
        json={"year": 2026, "month": 8, "amount": "1.00"},
        headers=headers
    )
    assert budget.status_code == 200

    create_transaction(
        client, headers, category_id, "0.10", "expense", "2026-08-15T12:00:00"
    )
    create_transaction(
        client, headers, category_id, "0.20", "expense", "2026-08-16T12:00:00"
    )

    summary = client.get(
        "/analytics/summary?start_date=2026-08-01&end_date=2026-08-31",
        headers=headers
    )
    assert summary.status_code == 200
    assert summary.json()["total_expenses"] == "0.30"
    assert summary.json()["budget_spent"] == "0.30"
    assert summary.json()["budget_remaining"] == "0.70"

    listed_budget = client.get("/budgets/", headers=headers)
    assert listed_budget.json()[0]["spent"] == "0.30"
    assert listed_budget.json()[0]["remaining"] == "0.70"


def test_budget_crud_and_duplicate_protection(client):
    register_user(client)
    headers = auth_headers(client)

    created = client.post(
        "/budgets/",
        json={"year": 2026, "month": 8, "amount": 10000},
        headers=headers
    )
    assert created.status_code == 200
    budget_id = created.json()["id"]
    assert created.json()["spent"] == "0.00"
    assert created.json()["remaining"] == "10000.00"
    assert created.json()["percentage"] == 0.0

    register_user(client, email="second@example.com")
    second_headers = auth_headers(client, email="second@example.com")
    other_user_budget = client.get(
        f"/budgets/{budget_id}",
        headers=second_headers
    )
    assert other_user_budget.status_code == 404

    duplicate = client.post(
        "/budgets/",
        json={"year": 2026, "month": 8, "amount": 12000},
        headers=headers
    )
    assert duplicate.status_code == 400

    listed = client.get("/budgets/", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.put(
        f"/budgets/{budget_id}",
        json={"year": 2026, "month": 9, "amount": 12000},
        headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["month"] == 9

    deleted = client.delete(
        f"/budgets/{budget_id}",
        headers=headers
    )
    assert deleted.status_code == 200

    assert client.get("/budgets/", headers=headers).json() == []


def test_over_budget_does_not_increase_available_cash(client):
    register_user(client)
    headers = auth_headers(client)
    category_id = create_category(client, headers, "Home")

    client.post(
        "/budgets/",
        json={"year": 2026, "month": 8, "amount": 1000},
        headers=headers
    )
    client.post(
        "/budgets/",
        json={"year": 2026, "month": 9, "amount": 2000},
        headers=headers
    )
    create_transaction(
        client, headers, category_id, 1200, "expense", "2026-08-15T12:00:00"
    )
    create_transaction(
        client, headers, category_id, 2000, "income", "2026-08-01T12:00:00"
    )

    summary = client.get(
        "/analytics/summary?start_date=2026-08-01&end_date=2026-09-30",
        headers=headers
    ).json()

    assert summary["cash_balance"] == "800.00"
    assert summary["budget_total"] == "3000.00"
    assert summary["budget_spent"] == "1200.00"
    assert summary["budget_remaining"] == "1800.00"
    assert summary["available_after_budgets"] == "-1200.00"


def test_analytics_summary_and_category_totals(client):
    register_user(client)
    headers = auth_headers(client)
    food_id = create_category(client, headers, "Food")

    create_transaction(
        client, headers, food_id, 250, "expense", "2026-08-29T12:00:00"
    )
    create_transaction(
        client, headers, food_id, 1000, "income", "2026-08-28T12:00:00"
    )

    summary = client.get(
        "/analytics/summary?start_date=2026-08-01&end_date=2026-08-31",
        headers=headers
    )
    assert summary.status_code == 200
    assert summary.json() == {
        "total_income": "1000.00",
        "total_expenses": "250.00",
        "balance": "750.00",
        "cash_balance": "750.00",
        "budget_total": "0.00",
        "budget_spent": "0.00",
        "budget_remaining": "0.00",
        "available_after_budgets": "750.00",
        "debt_borrowed": "0.00",
        "debt_lent": "0.00",
        "debt_interest": "0.00",
        "investment_contributions": "0.00",
        "investment_withdrawals": "0.00"
    }

    category_totals = client.get(
        "/analytics/by-category?start_date=2026-08-01&end_date=2026-08-31",
        headers=headers
    )
    assert category_totals.status_code == 200
    assert category_totals.json() == [
        {
            "category_id": food_id,
            "category_name": "Food",
            "total": "250.00"
        }
    ]


def test_debt_and_investment_transactions(client):
    register_user(client)
    headers = auth_headers(client)
    category_id = create_category(client, headers, "Finance")

    debt = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": 5000,
            "type": "debt",
            "debt_direction": "borrowed",
            "interest_amount": 250,
            "date": "2026-08-29T12:00:00"
        },
        headers=headers
    )
    assert debt.status_code == 200, debt.text
    assert debt.json()["debt_direction"] == "borrowed"
    assert debt.json()["interest_amount"] == "250.00"

    investment = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": 1500,
            "type": "investment",
            "investment_action": "contribution",
            "date": "2026-08-29T12:00:00"
        },
        headers=headers
    )
    assert investment.status_code == 200, investment.text

    lent_debt = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": 1000,
            "type": "debt",
            "debt_direction": "lent",
            "date": "2026-08-30T12:00:00"
        },
        headers=headers
    )
    assert lent_debt.status_code == 200, lent_debt.text

    withdrawal = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": 200,
            "type": "investment",
            "investment_action": "withdrawal",
            "date": "2026-08-31T12:00:00"
        },
        headers=headers
    )
    assert withdrawal.status_code == 200, withdrawal.text

    summary = client.get("/analytics/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["debt_borrowed"] == "5000.00"
    assert summary.json()["debt_lent"] == "1000.00"
    assert summary.json()["debt_interest"] == "250.00"
    assert summary.json()["investment_contributions"] == "1500.00"
    assert summary.json()["investment_withdrawals"] == "200.00"
    assert summary.json()["cash_balance"] == "2700.00"

    missing_direction = client.post(
        "/transactions/",
        json={
            "category_id": category_id,
            "amount": 100,
            "type": "debt",
            "date": "2026-08-29T12:00:00"
        },
        headers=headers
    )
    assert missing_direction.status_code == 422


def test_budget_spending_and_available_cash(client):
    register_user(client)
    headers = auth_headers(client)
    category_id = create_category(client, headers, "Home")

    created = client.post(
        "/budgets/",
        json={"year": 2026, "month": 8, "amount": 1000},
        headers=headers
    )
    assert created.status_code == 200

    create_transaction(
        client, headers, category_id, 250, "expense", "2026-08-15T12:00:00"
    )
    create_transaction(
        client, headers, category_id, 1000, "income", "2026-08-01T12:00:00"
    )

    budgets = client.get("/budgets/", headers=headers)
    assert budgets.status_code == 200
    assert budgets.json()[0]["spent"] == "250.00"
    assert budgets.json()[0]["remaining"] == "750.00"
    assert budgets.json()[0]["percentage"] == 25.0

    summary = client.get(
        "/analytics/summary?start_date=2026-08-01&end_date=2026-08-31",
        headers=headers
    )
    assert summary.status_code == 200
    assert summary.json()["cash_balance"] == "750.00"
    assert summary.json()["budget_total"] == "1000.00"
    assert summary.json()["budget_spent"] == "250.00"
    assert summary.json()["budget_remaining"] == "750.00"
    assert summary.json()["available_after_budgets"] == "0.00"

    deleted = client.delete(
        f"/budgets/{created.json()['id']}",
        headers=headers
    )
    assert deleted.status_code == 200
    assert client.get("/budgets/", headers=headers).json() == []

    after_delete = client.get(
        "/analytics/summary?start_date=2026-08-01&end_date=2026-08-31",
        headers=headers
    ).json()
    assert after_delete["budget_total"] == "0.00"
    assert after_delete["budget_spent"] == "0.00"
    assert after_delete["budget_remaining"] == "0.00"
    assert after_delete["available_after_budgets"] == "750.00"
