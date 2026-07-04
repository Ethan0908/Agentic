"use client";

import { useEffect, useMemo, useState } from "react";

type Website = {
  github_repo_name: string | null;
  github_repo_url: string | null;
  vercel_url: string | null;
  deployment_status: string;
  created_at: string;
};

type Business = {
  id: number;
  name: string;
  city: string | null;
  category: string | null;
  phone: string | null;
  website_url: string | null;
  latest_github_repo_name?: string | null;
  latest_github_repo_url?: string | null;
  latest_vercel_url?: string | null;
  latest_deployment_status?: string | null;
  status: string;
  created_at: string;
};

type Stats = {
  total: number;
  by_status: Record<string, number>;
};

function resolveApiBase() {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configured && !configured.includes("localhost")) {
    return configured;
  }
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return configured || "http://localhost:8000";
}

function latestWebsite(websites: Website[]) {
  return [...websites].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))[0] || null;
}

export default function DashboardPage() {
  const apiBase = useMemo(() => resolveApiBase(), []);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [keyword, setKeyword] = useState("dentist");
  const [location, setLocation] = useState("Vancouver");
  const [manualName, setManualName] = useState("");
  const [manualCategory, setManualCategory] = useState("");
  const [manualWebsite, setManualWebsite] = useState("");
  const [manualEmail, setManualEmail] = useState("");
  const [message, setMessage] = useState("Ready.");
  const [loading, setLoading] = useState(false);

  async function refresh() {
    const [businessResponse, statsResponse] = await Promise.all([
      fetch(`${apiBase}/businesses`, { cache: "no-store" }),
      fetch(`${apiBase}/stats`, { cache: "no-store" })
    ]);

    let nextBusinesses: Business[] = [];
    if (businessResponse.ok) {
      nextBusinesses = await businessResponse.json();
    }
    if (statsResponse.ok) {
      setStats(await statsResponse.json());
    }

    const enrichedBusinesses = await Promise.all(
      nextBusinesses.map(async (business) => {
        if (business.latest_vercel_url || business.latest_github_repo_url) {
          return business;
        }
        try {
          const websiteResponse = await fetch(`${apiBase}/businesses/${business.id}/websites`, { cache: "no-store" });
          if (!websiteResponse.ok) return business;
          const websites: Website[] = await websiteResponse.json();
          const latest = latestWebsite(websites);
          if (!latest) return business;
          return {
            ...business,
            latest_github_repo_name: latest.github_repo_name,
            latest_github_repo_url: latest.github_repo_url,
            latest_vercel_url: latest.vercel_url,
            latest_deployment_status: latest.deployment_status
          };
        } catch {
          return business;
        }
      })
    );

    setBusinesses(enrichedBusinesses);
  }

  useEffect(() => {
    refresh().catch(() => setMessage(`Could not reach backend at ${apiBase}. Check API_BASE_URL, Docker, and migrations.`));
  }, [apiBase]);

  async function runAction(label: string, action: () => Promise<Response>, openResult = false) {
    setLoading(true);
    setMessage(`${label}...`);
    try {
      const response = await action();
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || response.statusText);
      }
      const data = await response.json().catch(() => null);
      const url = data?.vercel_url || data?.github_repo_url;
      setMessage(url ? `${label} complete: ${url}` : `${label} complete.`);
      if (openResult && url && typeof window !== "undefined") {
        window.open(url, "_blank", "noopener,noreferrer");
      }
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Action failed");
    } finally {
      setLoading(false);
    }
  }

  async function discover() {
    await runAction("Discovering businesses", () =>
      fetch(`${apiBase}/discover`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword, location, max_results: 10, radius_m: 5000 })
      })
    );
  }

  async function createManualLead() {
    if (!manualName.trim()) {
      setMessage("Enter a business name first.");
      return;
    }
    await runAction("Creating manual lead", () =>
      fetch(`${apiBase}/businesses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: manualName,
          category: manualCategory || null,
          website_url: manualWebsite || null,
          contact_email: manualEmail || null,
          city: location
        })
      })
    );
    setManualName("");
    setManualCategory("");
    setManualWebsite("");
    setManualEmail("");
  }

  async function enrich(id: number) {
    await runAction("Finding emails", () => fetch(`${apiBase}/businesses/${id}/enrich-email`, { method: "POST" }));
  }

  async function validateEmails(id: number) {
    await runAction("Validating emails", () => fetch(`${apiBase}/businesses/${id}/validate-emails`, { method: "POST" }));
  }

  async function buildSite(id: number) {
    await runAction(
      "Building with Codex, publishing GitHub repo, and deploying Vercel",
      () => fetch(`${apiBase}/businesses/${id}/build-site`, { method: "POST" }),
      true
    );
  }

  async function draftEmail(id: number) {
    await runAction("Creating local email draft", () =>
      fetch(`${apiBase}/businesses/${id}/draft-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ use_gpt: false })
      })
    );
  }

  async function sendEmail(id: number) {
    await runAction("Sending latest email", () => fetch(`${apiBase}/businesses/${id}/send-latest-email`, { method: "POST" }));
  }

  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Raspberry Pi controller</p>
          <h1>Agentic Business Website Maker</h1>
          <p className="subtitle">Find businesses, generate category-specific sites with Codex, publish GitHub repos, deploy Vercel sites, draft outreach, and track cleanup.</p>
          <p className="hint">API: {apiBase}</p>
        </div>
        <div className="statusBox">
          <strong>{stats?.total ?? 0}</strong>
          <span>total leads</span>
        </div>
      </section>

      <section className="panel gridTwo">
        <div>
          <h2>Discover leads</h2>
          <div className="formRow">
            <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="keyword" />
            <input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="city" />
            <button onClick={discover} disabled={loading}>Discover</button>
          </div>
          <p className="hint">Requires GOOGLE_PLACES_API_KEY in .env. The search keyword and Places category are passed to Codex for classification.</p>
        </div>
        <div>
          <h2>Manual lead</h2>
          <div className="formRow">
            <input value={manualName} onChange={(event) => setManualName(event.target.value)} placeholder="business name" />
            <input value={manualCategory} onChange={(event) => setManualCategory(event.target.value)} placeholder="business type, e.g. sushi restaurant" />
            <input value={manualWebsite} onChange={(event) => setManualWebsite(event.target.value)} placeholder="optional original website URL" />
            <input value={manualEmail} onChange={(event) => setManualEmail(event.target.value)} placeholder="contact email" />
            <button onClick={createManualLead} disabled={loading}>Add</button>
          </div>
          <p className="hint">For manual leads, add a business type like sushi restaurant, dentist, salon, or plumber so Codex builds the right site.</p>
        </div>
      </section>

      <section className="panel">
        <div className="panelHeader">
          <h2>Pipeline</h2>
          <button onClick={refresh} disabled={loading}>Refresh</button>
        </div>
        <div className="statusGrid">
          {stats && Object.entries(stats.by_status).filter(([, count]) => count > 0).map(([status, count]) => (
            <div className="miniCard" key={status}>
              <strong>{count}</strong>
              <span>{status}</span>
            </div>
          ))}
        </div>
        <p className="message">{message}</p>
      </section>

      <section className="panel">
        <h2>Leads</h2>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Business</th>
                <th>Status</th>
                <th>Phone</th>
                <th>Generated site</th>
                <th>Original</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {businesses.map((business) => (
                <tr key={business.id}>
                  <td>
                    <strong>{business.name}</strong>
                    <span>{business.category || business.city || "No category"}</span>
                  </td>
                  <td><code>{business.latest_deployment_status || business.status}</code></td>
                  <td>{business.phone ? <a href={`tel:${business.phone}`}>{business.phone}</a> : "—"}</td>
                  <td>
                    {business.latest_vercel_url ? <a href={business.latest_vercel_url} target="_blank">Vercel</a> : null}
                    {business.latest_vercel_url && business.latest_github_repo_url ? " · " : null}
                    {business.latest_github_repo_url ? <a href={business.latest_github_repo_url} target="_blank">GitHub</a> : null}
                    {!business.latest_vercel_url && !business.latest_github_repo_url ? "—" : null}
                  </td>
                  <td>{business.website_url ? <a href={business.website_url} target="_blank">Original</a> : "—"}</td>
                  <td className="actions">
                    <button onClick={() => enrich(business.id)} disabled={loading || !business.website_url}>Find email</button>
                    <button onClick={() => validateEmails(business.id)} disabled={loading}>Validate</button>
                    <button onClick={() => buildSite(business.id)} disabled={loading}>Build + deploy</button>
                    <button onClick={() => draftEmail(business.id)} disabled={loading}>Draft</button>
                    <button onClick={() => sendEmail(business.id)} disabled={loading}>Send</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
