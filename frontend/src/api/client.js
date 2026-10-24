import { getUserTimeZone } from "../utils/dateUtils";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export function getAuthToken() {
  return localStorage.getItem("studysense_token");
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem("studysense_token", token);
  } else {
    localStorage.removeItem("studysense_token");
  }
}

export function getCurrentUser() {
  const userJson = localStorage.getItem("studysense_user");
  return userJson ? JSON.parse(userJson) : null;
}

export function setCurrentUser(user) {
  if (user) {
    localStorage.setItem("studysense_user", JSON.stringify(user));
  } else {
    localStorage.removeItem("studysense_user");
  }
}

export async function apiRequest(endpoint, options = {}) {
  const token = getAuthToken();
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    "X-Timezone": getUserTimeZone(),
    ...(options.headers || {}),
  };

  // Candidates to try: primary API_BASE, then direct IPv4, then direct localhost
  const candidateUrls = [
    `${API_BASE}${endpoint}`,
    `http://127.0.0.1:8000/api/v1${endpoint}`,
    `http://localhost:8000/api/v1${endpoint}`,
  ];

  let lastError = null;
  let response = null;

  for (const url of candidateUrls) {
    try {
      response = await fetch(url, {
        ...options,
        headers,
      });
      // If we got an HTTP response (even 4xx/5xx), the server was reached!
      break;
    } catch (networkErr) {
      lastError = networkErr;
      // Try next candidate
    }
  }

  if (!response) {
    console.error(`All connection attempts failed for ${endpoint}:`, lastError);
    throw new Error(
      "Unable to connect to AI StudySense backend. Please ensure the backend server is running on http://localhost:8000."
    );
  }

  if (!response.ok) {
    let errorDetail = `Request failed (${response.status})`;
    try {
      const err = await response.json();
      errorDetail = err.detail || err.message || errorDetail;
    } catch {
      // fallback
    }

    // Auto-refresh token if 401 encountered and not already attempting refresh or login
    if (response.status === 401 && !options._isRetry && !endpoint.startsWith("/auth/")) {
      try {
        console.info("Authentication token expired. Attempting automatic session renewal...");
        const refreshHeaders = {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        };
        const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: refreshHeaders,
        });
        if (refreshRes.ok) {
          const refreshData = await refreshRes.json();
          if (refreshData.access_token) {
            setAuthToken(refreshData.access_token);
            console.info("Authentication session renewed successfully. Retrying request.");
            return apiRequest(endpoint, {
              ...options,
              _isRetry: true,
            });
          }
        }
      } catch (refreshErr) {
        console.warn("Auto-refresh attempt failed:", refreshErr);
      }

      console.warn("Authentication session expired or invalid token.");
    }

    throw new Error(errorDetail);
  }

  return response.json();
}
