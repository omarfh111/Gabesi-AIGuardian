const API_BASE = "http://127.0.0.1:8000";

export async function fetchUserData() {
  const res = await fetch(`${API_BASE}/user-data`);
  if (!res.ok) throw new Error("Failed to fetch user data");
  return res.json();
}

export async function runParallelAnalysis(userData = null) {
  const res = await fetch(`${API_BASE}/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: userData ? JSON.stringify(userData) : "{}",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Analysis failed");
  }
  return res.json();
}

export async function runEnvAnalysis(userData = null) {
  const res = await fetch(`${API_BASE}/analyse/env`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: userData ? JSON.stringify(userData) : "{}",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Env analysis failed");
  }
  return res.json();
}

export async function runFinanceAnalysis(userData = null) {
  const res = await fetch(`${API_BASE}/analyse/finance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: userData ? JSON.stringify(userData) : "{}",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Finance analysis failed");
  }
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("API unreachable");
  return res.json();
}
