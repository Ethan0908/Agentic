"use client";

import { useEffect, useMemo, useState } from "react";

type Website = {
  id: number;
  github_repo_name: string | null;
  github_repo_url: string | null;
  vercel_url: string | null;
  deployment_status: string;
  created_at: string;
};

type Contact = {
  id: number;
  email: string | null;
  phone: string | null;
  validation_status: string;
};

type Business = {
  id: number;
  name: string;
  city: string | null;
  category: string | null;
  phone: string | null;
  website_url: string | null;
  primary_email?: string | null;
  latest_website_id?: number | null;
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
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [queueStatus, setQueueStatus] = useState<string[]>([]);
  const [queueRunning, setQueueRunning] = useState(false);

  const selectedBusinesses = useMemo(
    () => businesses.filter((business) => selectedIds.has(business.id)),
    [businesses, selectedIds]
  );

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
        try {
          const [websiteResponse, contactsResponse] = await Promise.all([
            fetch(`${apiBase}/businesses/${business.id}/websites`, { cache: "no-store" }),
            fetch(`${apiBase}/businesses/${business.id}/contacts`, { cache: "no-store" })
          ]);

          let latest: Website | null = null;
          if (websiteResponse.ok) {
            const websites: Website[] = await websiteResponse.json();
            latest = latestWebsite(websites);
          }

          let contacts: Contact[] = [];
          if (contactsResponse.ok) {
            contacts = await contactsResponse.json();
          }
          const primaryEmail = contacts.find((contact) => contact.email)?.email || null;

          return {
            ...business,
            primary_email: primaryEmail,
            latest_website_id: latest?.id || null,
            latest_github_repo_name: latest?.github_repo_name || business.latest_github_repo_name,
            latest_github_repo_url: latest?.github_repo_url || business.latest_github_repo_url,
            latest_vercel_url: latest?.vercel_url || business.latest_vercel_url,
            latest_deployment_status: latest?.deployment_status || business.latest_deployment_status
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

  function toggleSelected(id: number) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function selectAllVisible() {
    setSelectedIds(new Set(businesses.map((business) => business.id)));
  }

  function clearSelected() {
    setSelectedIds(new Set());
  }

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

  async function runSelectedQueue(label: string, endpoint: (business: Business) => string, options?: RequestInit) {
    if (selectedBusinesses.length === 0) {
      setMessage("Select at least one company first.");
      return;
    }

    setLoading(true);
    setQueueRunning(true);
    setQueueStatus([]);

    const results: string[] = [];
    for (let index = 0; index < selectedBusinesses.length; index += 1) {
      const business = selectedBusinesses[index];
      const prefix = `${index + 1}/${selectedBusinesses.length} ${business.name}`;
      setMessage(`${label}: ${prefix}`);

      try {
        const response = await fetch(endpoint(business), { method: "POST", ...(options || {}) });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(error.detail || response.statusText);
        }
        const data = await response.json().catch(() => null);
        const url = data?.vercel_url || data?.github_repo_url;
        results.push(`✅ ${prefix}${url ? ` — ${url}` : ""}`);
      } catch (error) {
        results.push(`❌ ${prefix} — ${error instanceof Error ? error.message : "failed"}`);
      }
      setQueueStatus([...results]);
      await refresh();
    }

    setMessage(`${label} queue finished.`);
    setLoading(false);
    setQueueRunning(false);
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

  async function deleteSelectedSites() {
    if (selectedBusinesses.length === 0) {
      setMessage("Select at least one company first.");
      return;
    }
    if (!window.confirm(`Delete generated GitHub/Vercel site for ${selectedBusinesses.length} selected company/companies?`)) {
      return;
    }
    await runSelectedQueue("Deleting generated sites", (business) => `${apiBase}/businesses/${business.id}/delete-latest-site`);
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
            <input value={manualCategory} onChange={(event) => setManualCategory(event.target.value)} placeholder="business type, e.g. plumber" />
            <input value={manualWebsite} onChange={(event) => setManualWebsite(event.target.value)} placeholder="optional original website URL" />
            <input value={manualEmail} onChange={(event) => setManualEmail(event.target.value)} placeholder="contact email" />
            <button onClick={createManualLead} disabled={loading}>Add</button>
          </div>
          <p className="hint">For manual leads, add a specific business type so Codex builds the right site and not a generic recycled layout.</p>
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
        {queueStatus.length > 0 && (
          <div className="queueLog">
            {queueStatus.map((line) => <p key={line}>{line}</p>)}
          </div>
        )}
      </section>

      <section className="panel leadsPanel">
        <div className="panelHeader">
          <h2>Leads</h2>
          <div className="inlineControls">
            <button type="button" onClick={selectAllVisible} disabled={loading || businesses.length === 0}>Select visible</button>
            <button type="button" onClick={clearSelected} disabled={loading || selectedIds.size === 0}>Clear</button>
          </div>
        </div>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th className="selectCol">Use</th>
                <th>Business</th>
                <th>Status</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Generated site</th>
                <th>Original</th>
              </tr>
            </thead>
            <tbody>
              {businesses.map((business) => (
                <tr key={business.id} className={selectedIds.has(business.id) ? "selectedRow" : ""}>
                  <td className="selectCol">
                    <label className="checkWrap" aria-label={`Select ${business.name}`}>
                      <input type="checkbox" checked={selectedIds.has(business.id)} onChange={() => toggleSelected(business.id)} />
                      <span>✓</span>
                    </label>
                  </td>
                  <td>
                    <strong>{business.name}</strong>
                    <span>{business.category || business.city || "No category"}</span>
                  </td>
                  <td><code>{business.latest_deployment_status || business.status}</code></td>
                  <td>{business.phone ? <a href={`tel:${business.phone}`}>{business.phone}</a> : "—"}</td>
                  <td>{business.primary_email ? <a href={`mailto:${business.primary_email}`}>{business.primary_email}</a> : "—"}</td>
                  <td>
                    {business.latest_vercel_url ? <a href={business.latest_vercel_url} target="_blank">Vercel</a> : null}
                    {business.latest_vercel_url && business.latest_github_repo_url ? " · " : null}
                    {business.latest_github_repo_url ? <a href={business.latest_github_repo_url} target="_blank">GitHub</a> : null}
                    {!business.latest_vercel_url && !business.latest_github_repo_url ? "—" : null}
                  </td>
                  <td>{business.website_url ? <a href={business.website_url} target="_blank">Original</a> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="floatingActions" aria-label="Selected company actions">
        <div className="selectionSummary">{selectedIds.size} selected</div>
        <button onClick={() => runSelectedQueue("Finding emails", (business) => `${apiBase}/businesses/${business.id}/enrich-email`)} disabled={loading || selectedIds.size === 0}>Find email</button>
        <button onClick={() => runSelectedQueue("Validating emails", (business) => `${apiBase}/businesses/${business.id}/validate-emails`)} disabled={loading || selectedIds.size === 0}>Validate</button>
        <button onClick={() => runSelectedQueue("Building sites", (business) => `${apiBase}/businesses/${business.id}/build-site`)} disabled={loading || selectedIds.size === 0}>Build</button>
        <button onClick={() => runSelectedQueue("Drafting emails", (business) => `${apiBase}/businesses/${business.id}/draft-email`, { headers: { "Content-Type": "application/json" }, body: JSON.stringify({ use_gpt: false }) })} disabled={loading || selectedIds.size === 0}>Draft</button>
        <button onClick={() => runSelectedQueue("Sending emails", (business) => `${apiBase}/businesses/${business.id}/send-latest-email`)} disabled={loading || selectedIds.size === 0}>Send</button>
        <button className="danger" onClick={deleteSelectedSites} disabled={loading || selectedIds.size === 0 || queueRunning}>Delete site</button>
      </div>
    </main>
  );
}
