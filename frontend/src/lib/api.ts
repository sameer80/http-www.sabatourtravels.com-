const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Token = { access_token: string };

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

function formatApiError(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item))).join(", ");
  }
  return "Request failed";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error(`Cannot reach API at ${API_URL}. Is the backend running on port 8000?`);
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(formatApiError(err.detail) || res.statusText);
  }
  return res.json();
}

export const api = {
  register: (data: { email: string; password: string; full_name?: string; organization?: string }) =>
    request("/api/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw new Error("Login failed");
    return res.json() as Promise<Token>;
  },
  me: () => request<{ email: string; full_name: string }>("/api/auth/me"),
  websites: () => request<any[]>("/api/websites"),
  createWebsite: (data: any) => request("/api/websites", { method: "POST", body: JSON.stringify(data) }),
  dashboard: (id: number) => request(`/api/websites/${id}/dashboard`),
  startCrawl: (id: number) => request(`/api/websites/${id}/crawl`, { method: "POST" }),
  issues: (id: number) => request<any[]>(`/api/websites/${id}/issues`),
  pages: (id: number) => request<any[]>(`/api/websites/${id}/pages`),
  keywords: (id: number) => request<any[]>(`/api/websites/${id}/keywords`),
  addKeyword: (id: number, data: any) =>
    request(`/api/websites/${id}/keywords`, { method: "POST", body: JSON.stringify(data) }),
  opportunities: (id: number) => request<any[]>(`/api/websites/${id}/opportunities`),
  tasks: (id: number) => request<any[]>(`/api/websites/${id}/tasks`),
  updateTask: (websiteId: number, taskId: number, data: any) =>
    request(`/api/websites/${websiteId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  chat: (id: number, message: string, conversationId?: number) =>
    request(`/api/websites/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
  serpAnalysis: (id: number, keyword: string, pageId?: number) =>
    request(`/api/websites/${id}/serp-analysis`, {
      method: "POST",
      body: JSON.stringify({ keyword, page_id: pageId }),
    }),
  internalLinks: (id: number) => request<any[]>(`/api/websites/${id}/internal-links`),
  backlinkGap: (id: number) => request<any>(`/api/websites/${id}/backlinks/gap`),
  searchLinkProspects: (id: number, data: any) =>
    request(`/api/websites/${id}/link-prospects/search`, { method: "POST", body: JSON.stringify(data) }),
  linkProspects: (id: number, minDa = 0) =>
    request<any[]>(`/api/websites/${id}/link-prospects?min_da=${minDa}`),
  updateLinkProspect: (websiteId: number, prospectId: number, data: any) =>
    request(`/api/websites/${websiteId}/link-prospects/${prospectId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
