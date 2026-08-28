const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Token = { access_token: string };

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
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
};
