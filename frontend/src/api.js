const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const TOKEN_KEY = "expense_token";

async function parseResponse(response) {
  if (response.status === 204) {
    return null;
  }

  let payload = null;

  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail = payload?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(", ")
      : detail || "Something went wrong. Please try again.";

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return payload;
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = localStorage.getItem(TOKEN_KEY);

  // Token ko ek hi jagah attach karne se protected requests consistent rehti hain.
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", "Bearer " + token);
  }

  const response = await fetch(API_URL + path, {
    ...options,
    headers
  });

  return parseResponse(response);
}

function writeJson(path, method, payload) {
  return apiRequest(path, {
    method,
    body: JSON.stringify(payload)
  });
}

function queryString(params) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      query.set(key, value);
    }
  });

  const result = query.toString();
  return result ? "?" + result : "";
}

export function login(email, password) {
  return apiRequest("/auth/login", {
    method: "POST",
    body: new URLSearchParams({
      username: email,
      password
    })
  });
}

export function register(payload) {
  return writeJson("/users/", "POST", payload);
}

export function getCurrentUser() {
  return apiRequest("/users/me");
}

export function getCategories() {
  return apiRequest("/categories/");
}

export function createCategory(name) {
  return writeJson("/categories/", "POST", { name });
}

export function deleteCategory(categoryId) {
  return apiRequest("/categories/" + categoryId, { method: "DELETE" });
}

export function getTransactions(params = {}) {
  return apiRequest("/transactions/" + queryString(params));
}

export function createTransaction(payload) {
  return writeJson("/transactions/", "POST", payload);
}

export function deleteTransaction(transactionId) {
  return apiRequest("/transactions/" + transactionId, { method: "DELETE" });
}

export function getBudgets() {
  return apiRequest("/budgets/");
}

export function createBudget(payload) {
  return writeJson("/budgets/", "POST", payload);
}

export function deleteBudget(budgetId) {
  return apiRequest("/budgets/" + budgetId, { method: "DELETE" });
}

export function getSummary(params = {}) {
  return apiRequest("/analytics/summary" + queryString(params));
}

export function getCategoryTotals(params = {}) {
  return apiRequest("/analytics/by-category" + queryString(params));
}
