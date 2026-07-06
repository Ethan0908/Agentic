"use client";

import { FormEvent, useEffect, useMemo, useState } from 'react';

type ClientStatus = 'lead' | 'queued' | 'generating' | 'generated' | 'emailed' | 'error';
type ViewMode = 'finder' | 'sheet' | 'ui';

type ClientRecord = {
  id: string;
  name: string;
  businessType: string;
  city: string;
  serviceArea: string;
  website: string;
  email: string;
  phone: string;
  notes: string;
  photos: string[];
  status: ClientStatus;
  error?: string;
  generatedSitePath?: string;
  createdAt: string;
  updatedAt: string;
};

const EMPTY = { name: '', businessType: '', city: '', serviceArea: '', website: '', email: '', phone: '', notes: '', photos: '' };
const STATUS_LABELS: Record<ClientStatus, string> = { lead: 'Lead', queued: 'Queued', generating: 'Generating', generated: 'Generated', emailed: 'Emailed', error: 'Error' };

function splitPhotos(value: string) {
  return value.split(/\n|,/).map((item) => item.trim()).filter(Boolean);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-CA', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value));
}

export default function Home() {
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [form, setForm] = useState(EMPTY);
  const [finder, setFinder] = useState({ query: '', location: '', limit: '20' });
  const [view, setView] = useState<ViewMode>('sheet');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [finding, setFinding] = useState(false);
  const [generatingId, setGeneratingId] = useState('');
  const [error, setError] = useState('');

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return clients;
    return clients.filter((client) => [client.name, client.businessType, client.city, client.serviceArea, client.website, client.email, client.phone, client.notes, client.status].join(' ').toLowerCase().includes(q));
  }, [clients, search]);

  const counts = useMemo(() => ({
    total: clients.length,
    lead: clients.filter((client) => client.status === 'lead').length,
    queued: clients.filter((client) => client.status === 'queued').length,
    generating: clients.filter((client) => client.status === 'generating').length,
    generated: clients.filter((client) => client.status === 'generated').length,
    error: clients.filter((client) => client.status === 'error').length,
  }), [clients]);

  async function loadClients() {
    setLoading(true);
    const response = await fetch('/api/clients', { cache: 'no-store' });
    const payload = await response.json();
    setClients(payload.clients || []);
    setLoading(false);
  }

  useEffect(() => {
    loadClients().catch((err) => {
      setError(err instanceof Error ? err.message : 'Unable to load clients.');
      setLoading(false);
    });
  }, []);

  async function createClient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError('');
    const response = await fetch('/api/clients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, photos: splitPhotos(form.photos) }),
    });
    const payload = await response.json();
    if (!response.ok) setError(payload.error || 'Unable to create client.');
    else {
      setClients((current) => [payload.client, ...current]);
      setForm(EMPTY);
      setView('sheet');
    }
    setSaving(false);
  }

  async function runLeadFinder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFinding(true);
    setError('');
    const response = await fetch('/api/lead-finder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(finder),
    });
    const payload = await response.json();
    if (!response.ok) setError(payload.error || 'Lead finder failed.');
    else {
      await loadClients();
      setView('sheet');
    }
    setFinding(false);
  }

  async function generateClient(client: ClientRecord) {
    setGeneratingId(client.id);
    setError('');
    setClients((current) => current.map((item) => item.id === client.id ? { ...item, status: 'generating', error: '' } : item));
    const response = await fetch('/api/generate-site', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: client.id }),
    });
    const payload = await response.json();
    if (payload.client) setClients((current) => current.map((item) => item.id === client.id ? payload.client : item));
    if (!response.ok) setError(payload.error || 'Site generation failed.');
    setGeneratingId('');
  }

  async function setStatus(client: ClientRecord, status: ClientStatus) {
    const response = await fetch(`/api/clients/${client.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    const payload = await response.json();
    if (response.ok) setClients((current) => current.map((item) => item.id === client.id ? payload.client : item));
  }

  async function removeClient(client: ClientRecord) {
    const response = await fetch(`/api/clients/${client.id}`, { method: 'DELETE' });
    if (response.ok) setClients((current) => current.filter((item) => item.id !== client.id));
  }

  return (
    <main className="shell">
      <section className="topbar">
        <div className="tabs">
          <button className={view === 'finder' ? 'active' : ''} onClick={() => setView('finder')}>Lead Finder</button>
          <button className={view === 'sheet' ? 'active' : ''} onClick={() => setView('sheet')}>Spreadsheet</button>
          <button className={view === 'ui' ? 'active' : ''} onClick={() => setView('ui')}>UI Cards</button>
        </div>
        <div className="toolbar">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search leads..." />
          <button className="ghost" onClick={loadClients} disabled={loading}>{loading ? 'Loading…' : 'Reload'}</button>
        </div>
      </section>

      <section className="stats compact">
        <article><strong>{counts.total}</strong><span>Total</span></article>
        <article><strong>{counts.lead}</strong><span>Leads</span></article>
        <article><strong>{counts.queued}</strong><span>Queued</span></article>
        <article><strong>{counts.generating}</strong><span>Generating</span></article>
        <article><strong>{counts.generated}</strong><span>Generated</span></article>
        <article><strong>{counts.error}</strong><span>Errors</span></article>
      </section>

      {error ? <p className="error banner">{error}</p> : null}

      {view === 'finder' ? (
        <section className="grid">
          <form className="panel form" onSubmit={runLeadFinder}>
            <div><p className="eyebrow">Automatic lead finder</p><h2>Find leads</h2></div>
            <label>Business / niche<input value={finder.query} onChange={(event) => setFinder({ ...finder, query: event.target.value })} placeholder="omakase restaurants, emergency plumbers..." /></label>
            <label>Location<input value={finder.location} onChange={(event) => setFinder({ ...finder, location: event.target.value })} placeholder="New York, Manhattan..." /></label>
            <label>Limit<input value={finder.limit} onChange={(event) => setFinder({ ...finder, limit: event.target.value })} /></label>
            <button type="submit" disabled={finding}>{finding ? 'Finding…' : 'Run Lead Finder'}</button>
            <p className="notes">Uses LEAD_FINDER_COMMAND on the Pi and imports JSON leads into the spreadsheet.</p>
          </form>

          <form className="panel form" onSubmit={createClient}>
            <div><p className="eyebrow">Manual add</p><h2>Add one lead</h2></div>
            <label>Business name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required /></label>
            <label>Business type<input value={form.businessType} onChange={(event) => setForm({ ...form, businessType: event.target.value })} /></label>
            <div className="two-col"><label>City<input value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} /></label><label>Service area<input value={form.serviceArea} onChange={(event) => setForm({ ...form, serviceArea: event.target.value })} /></label></div>
            <label>Website<input value={form.website} onChange={(event) => setForm({ ...form, website: event.target.value })} /></label>
            <div className="two-col"><label>Email<input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label><label>Phone<input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label></div>
            <label>Photo URLs<textarea value={form.photos} onChange={(event) => setForm({ ...form, photos: event.target.value })} /></label>
            <label>Notes<textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label>
            <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save Lead'}</button>
          </form>
        </section>
      ) : null}

      {view === 'sheet' ? (
        <section className="panel sheet-panel">
          <div className="list-heading"><div><p className="eyebrow">Lead sheet</p><h2>Spreadsheet tracker</h2></div><button className="ghost" onClick={loadClients}>Refresh</button></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Status</th><th>Business</th><th>Type</th><th>Area</th><th>Website</th><th>Contact</th><th>Photos</th><th>Updated</th><th>Actions</th></tr></thead>
              <tbody>
                {filtered.map((client) => (
                  <tr key={client.id}>
                    <td><span className={`status ${client.status}`}>{STATUS_LABELS[client.status]}</span></td>
                    <td><strong>{client.name}</strong>{client.generatedSitePath ? <small>{client.generatedSitePath}</small> : null}{client.error ? <small className="error">{client.error}</small> : null}</td>
                    <td>{client.businessType || '—'}</td>
                    <td>{client.serviceArea || client.city || '—'}</td>
                    <td>{client.website ? <a href={client.website} target="_blank" rel="noreferrer">Open</a> : '—'}</td>
                    <td>{client.email || client.phone || '—'}</td>
                    <td>{client.photos.length}</td>
                    <td>{formatDate(client.updatedAt)}</td>
                    <td className="row-actions"><button onClick={() => generateClient(client)} disabled={generatingId === client.id || client.status === 'generating'}>{generatingId === client.id || client.status === 'generating' ? 'Generating…' : 'Generate'}</button><button onClick={() => setStatus(client, 'queued')}>Queue</button><button className="danger" onClick={() => removeClient(client)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!filtered.length ? <div className="empty-state"><h3>No matching leads.</h3><p>Run the lead finder or add a lead manually.</p></div> : null}
        </section>
      ) : null}

      {view === 'ui' ? (
        <section className="client-list cards-grid">
          {filtered.map((client) => (
            <article className="client-card" key={client.id}>
              <div className="client-topline"><div><h3>{client.name}</h3><p>{client.businessType || 'Business type missing'} · {client.serviceArea || client.city || 'Area missing'}</p></div><span className={`status ${client.status}`}>{STATUS_LABELS[client.status]}</span></div>
              <div className="meta-row"><span>{client.photos.length} photos</span><span>{client.website || 'No website'}</span></div>
              {client.notes ? <p className="notes">{client.notes}</p> : null}
              {client.generatedSitePath ? <p className="notes">Generated path: {client.generatedSitePath}</p> : null}
              {client.error ? <p className="error">{client.error}</p> : null}
              <div className="actions"><button onClick={() => generateClient(client)} disabled={generatingId === client.id || client.status === 'generating'}>{generatingId === client.id || client.status === 'generating' ? 'Generating…' : 'Generate Site'}</button><button onClick={() => setStatus(client, 'queued')}>Queue</button><button onClick={() => setStatus(client, 'generated')}>Mark generated</button><button className="danger" onClick={() => removeClient(client)}>Delete</button></div>
            </article>
          ))}
        </section>
      ) : null}
    </main>
  );
}
