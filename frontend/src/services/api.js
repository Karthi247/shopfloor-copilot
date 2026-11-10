const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const localBackend =
  isLocalHost && window.location.port === '5173' ? 'http://127.0.0.1:8000/api' : '/api';
const API_BASE = import.meta.env.VITE_API_BASE_URL || localBackend;
const TOKEN_KEY = 'shopfloor-ai-copilot.auth-token.v1';

function expireSession() {
  localStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event('shopfloor-auth-expired'));
}

function authHeaders(headers = {}) {
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { ...headers, Authorization: `Bearer ${token}` } : headers;
}

async function readJson(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(
      `The API returned a non-JSON response (HTTP ${response.status}). Check that the backend is running at ${API_BASE}.`,
    );
  }
  return response.json();
}

export async function askCopilot(question, history = []) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ question, history }),
  });
  if (response.status === 401) expireSession();
  const data = await readJson(response);
  if (!response.ok) throw new Error(data.detail || 'Unable to reach the assistant.');
  return data;
}

export async function getHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error('Backend unavailable');
  return readJson(response);
}

export async function getDocuments() {
  const response = await fetch(`${API_BASE}/documents`, { headers: authHeaders() });
  if (response.status === 401) expireSession();
  const documents = await readJson(response);
  if (!response.ok)
    throw new Error(documents.detail || 'Unable to load indexed documents.');
  return documents;
}

async function postAuth(path, body) {
  const response = await fetch(`${API_BASE}/auth/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await readJson(response);
  if (!response.ok) throw new Error(data.detail || 'Authentication failed.');
  if (data.access_token) localStorage.setItem(TOKEN_KEY, data.access_token);
  return data;
}

export async function signUp({ name, email, password }) {
  return postAuth('signup', { name, email, password });
}

export async function signIn({ email, password }) {
  return postAuth('login', { email, password });
}

export async function getCurrentUser() {
  if (!localStorage.getItem(TOKEN_KEY)) return null;
  const response = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }
  const data = await readJson(response);
  if (!response.ok) throw new Error(data.detail || 'Unable to load your account.');
  return data;
}

export async function updateCurrentUser({ name, email }) {
  const response = await fetch(`${API_BASE}/auth/me`, {
    method: 'PATCH',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ name, email }),
  });
  if (response.status === 401) expireSession();
  const data = await readJson(response);
  if (!response.ok) throw new Error(data.detail || 'Unable to update your profile.');
  return data;
}

export async function updatePassword({ current_password, new_password }) {
  const response = await fetch(`${API_BASE}/auth/password`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ current_password, new_password }),
  });
  if (response.status === 401) expireSession();
  const data = await readJson(response);
  if (!response.ok) throw new Error(data.detail || 'Unable to change your password.');
  return data;
}

export function signOut() {
  localStorage.removeItem(TOKEN_KEY);
}
