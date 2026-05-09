const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const DEV_ORG_ID = process.env.NEXT_PUBLIC_DEV_ORG_ID || "dev-org-001";
export const DEV_USER_ID = process.env.NEXT_PUBLIC_DEV_USER_ID || "dev-user-001";
export const DEV_USER_ROLE = process.env.NEXT_PUBLIC_DEV_USER_ROLE || "admin";

// TODO: replace DEV_* headers with real auth token when auth is implemented

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let _currentRole: string = DEV_USER_ROLE;

export function setApiRole(role: string) {
  _currentRole = role;
}

function authHeaders(): HeadersInit {
  return {
    "X-Org-ID": DEV_ORG_ID,
    "X-User-ID": DEV_USER_ID,
    "X-User-Role": _currentRole,
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail ?? body.message ?? message;
    } catch {
      // ignore parse failure
    }
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get<T>(path: string): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: "GET",
      headers: { "Content-Type": "application/json", ...authHeaders() },
    }).then((r) => handleResponse<T>(r));
  },

  post<T>(path: string, body?: unknown): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }).then((r) => handleResponse<T>(r));
  },

  patch<T>(path: string, body?: unknown): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }).then((r) => handleResponse<T>(r));
  },

  delete<T>(path: string): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json", ...authHeaders() },
    }).then((r) => handleResponse<T>(r));
  },

  upload<T>(path: string, formData: FormData): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { ...authHeaders() },
      body: formData,
    }).then((r) => handleResponse<T>(r));
  },

  put<T>(path: string, body?: unknown): Promise<T> {
    return fetch(`${BASE_URL}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }).then((r) => handleResponse<T>(r));
  },
};

// TODO: implement backend PUT endpoints for content editing
export const contentEditorApi = {
  saveChapter: (_chapterNumber: number, _content: string): Promise<{ ok: true }> =>
    Promise.resolve({ ok: true }),
  saveQuizSet: (_quizId: string, _questions: unknown[]): Promise<{ ok: true }> =>
    Promise.resolve({ ok: true }),
  saveChecklist: (_categories: unknown[]): Promise<{ ok: true }> =>
    Promise.resolve({ ok: true }),
};
