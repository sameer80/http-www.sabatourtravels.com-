"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo1234");
  const [fullName, setFullName] = useState("Demo User");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [backendReady, setBackendReady] = useState<boolean | null>(null);

  useEffect(() => {
    if (localStorage.getItem("token")) router.push("/dashboard");
  }, [router]);

  useEffect(() => {
    api.health().then(setBackendReady);
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (mode === "register") {
        await api.register({ email, password, full_name: fullName });
      }
      const token = await api.login(email, password);
      localStorage.setItem("token", token.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-brand-900 p-6">
      <form onSubmit={submit} className="card w-full max-w-md space-y-4">
        <div>
          <h1 className="text-2xl font-bold">AI SEO Manager</h1>
          <p className="text-sm text-slate-400">Evidence-based SEO intelligence and action management</p>
        </div>
        {backendReady === false && (
          <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-200">
            Backend is not running on port 8000. Run <strong>scripts/start-local-windows.bat</strong>, wait for the
            Backend PowerShell window to finish, then refresh this page.
          </p>
        )}
        {mode === "register" && (
          <input className="input" placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        )}
        <input className="input" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="input" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="btn w-full" disabled={loading}>{loading ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}</button>
        <button type="button" className="text-sm text-brand-500" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
