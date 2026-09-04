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
    assert [item["id"] for item in all_transactions.json()] == [
        later_expense["id"], expense["id"], income["id"]
    ]

    expense_filter = client.get(
        "/transactions/?type=expense",
        headers=headers
    )
    assert len(expense_filter.json()) == 2

    category_filter = client.get(
        f"/transactions/?category_id={food_id}",
        headers=headers
    )
    assert len(category_filter.json()) == 2

    date_filter = client.get(
        "/transactions/?start_date=2026-08-01&end_date=2026-08-31",
        headers=headers
    )
    assert len(date_filter.json()) == 2

    page = client.get(
        "/transactions/?skip=1&limit=1",
        headers=headers
    )
    assert [item["id"] for item in page.json()] == [expense["id"]]

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

    summary = client.get("/analytics/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["debt_borrowed"] == "5000.00"
    assert summary.json()["debt_interest"] == "250.00"
    assert summary.json()["investment_contributions"] == "1500.00"
    assert summary.json()["cash_balance"] == "3500.00"

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
