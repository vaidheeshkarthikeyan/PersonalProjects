/**
 * API client — Axios wrapper for the Flask backend.
 *
 * All functions return Promises that resolve to the response data.
 * Base URL defaults to http://localhost:5000/api for local development.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ===================================================================
// Dashboard endpoints
// ===================================================================

/** Fetch lifetime KPI summary. */
export async function fetchKpis() {
  const { data } = await api.get('/dashboard/kpis');
  return data;
}

/** Fetch 7-day trailing application volume for the bar chart. */
export async function fetchVolume() {
  const { data } = await api.get('/dashboard/volume');
  return data;
}

/**
 * Fetch paginated application logs.
 * @param {number} page - Page number (1-indexed).
 * @param {number} perPage - Items per page.
 * @param {string|null} status - Filter by status (SUCCESS, SKIPPED, FAILED).
 * @param {string|null} search - Text search on company/title.
 */
export async function fetchLogs(page = 1, perPage = 20, status = null, search = null) {
  const params = { page, per_page: perPage };
  if (status) params.status = status;
  if (search) params.search = search;
  const { data } = await api.get('/dashboard/logs', { params });
  return data;
}

// ===================================================================
// Bot control endpoints
// ===================================================================

/**
 * Start the automation bot.
 * @param {string} searchQuery - Comma-separated keywords.
 */
export async function startBot(searchQuery) {
  const { data } = await api.post('/bot/start', { search_query: searchQuery });
  return data;
}

/** Stop the running bot gracefully. */
export async function stopBot() {
  const { data } = await api.post('/bot/stop');
  return data;
}

/** Get current bot status and active run info. */
export async function getBotStatus() {
  const { data } = await api.get('/bot/status');
  return data;
}

export default api;
