"use client";

import { FormEvent, useEffect, useMemo, useState } from 'react';

type ClientStatus = 'lead' | 'queued' | 'generating' | 'generated' | 'emailed' | 'error';

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

type FormState = {
  name: string;
  businessType: string;
  city: string;
  serviceArea: string;
  website: string;
  email: string;
  phone: string;
  notes: string;
  photos: string;
};

const EMPTY_FORM: FormState = {
  name: '',
  businessType: '',
  city: '',
  serviceArea: '',
  website: '',
  email: '',
  phone: '',
  notes: '',
  photos: '',
};

const STATUS_LABELS: Record<ClientStatus, string> = {
  lead: 'Lead',
  queued: 'Queued',
  generating: 'Generating',
  generated: 'Generated',
  emailed: 'Emailed',
  error: 'Error',
};

function splitPhotos(value: string) {
  return value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-CA', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value));
}

export default function Home() {
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const queuedCount = useMemo(() => clients.filter((client) => client.status === 'queued').length, [clients]);
  const activeCount = useMemo(() => clients.filter((client) => client.status === 'generating').length, [clients]);

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
      body: JSON.stringify({
        name: form.name,
        businessType: form.businessType,
        city: form.city,
        serviceArea: form.serviceArea,
        website: form.website,
        email: form.email,
        phone: form.phone,
        notes: form.notes,
        photos: splitPhotos(form.photos),
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      setError(payload.error || 'Unable to create client.');
      setSaving(false);
      return;
    }

    setClients((current) => [payload.client, ...current]);
    setForm(EMPTY_FORM);
    setSaving(false);
  }

  async function setStatus(client: ClientRecord, status: ClientStatus) {
    const response = await fetch(`/api/clients/${client.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    const payload = await response.json();
    if (response.ok) {
      setClients((current) => current.map((item) => (item.id === client.id ? payload.client : item)));
    }
  }

  async function removeClient(client: ClientRecord) {
    const response = await fetch(`/api/clients/${client.id}`, { method: 'DELETE' });
    if (response.ok) {
      setClients((current) => current.filter((item) => item.id !== client.id));
    }
  }

  return (
    <main className="shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Agentic Website Builder</p>
          <h1>Clients, queue state, and site inputs on port 3000.</h1>
          <p className="lede">
            The Pi can host this control panel, keep only runtime client data locally, and pull all code from GitHub.
          </p>
        </div>
        <div className="stats">
          <article>
            <strong>{clients.length}</strong>
            <span>Total clients</span>
          </article>
          <article>
            <strong>{queuedCount}</strong>
            <span>Queued</span>
          </article>
          <article>
            <strong>{activeCount}</strong>
            <span>Generating</span>
          </article>
        </div>
      </section>

      <section className="grid">
        <form className="panel form" onSubmit={createClient}>
          <div>
            <p className="eyebrow">New client</p>
            <h2>Add a business</h2>
          </div>

          <label>
            Business name
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label>
            Business type
            <input value={form.businessType} onChange={(event) => setForm({ ...form, businessType: event.target.value })} placeholder="emergency plumber, salon, dentist..." />
          </label>
          <div className="two-col">
            <label>
              City
              <input value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} />
            </label>
            <label>
              Service area
              <input value={form.serviceArea} onChange={(event) => setForm({ ...form, serviceArea: event.target.value })} />
            </label>
          </div>
          <label>
            Website
            <input value={form.website} onChange={(event) => setForm({ ...form, website: event.target.value })} placeholder="https://..." />
          </label>
          <div className="two-col">
            <label>
              Email
              <input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </label>
            <label>
              Phone
              <input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
            </label>
          </div>
          <label>
            Photo URLs
            <textarea value={form.photos} onChange={(event) => setForm({ ...form, photos: event.target.value })} placeholder="One public business image URL per line" />
          </label>
          <label>
            Notes
            <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Lead source, offer, target customer, email angle..." />
          </label>

          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save client'}</button>
        </form>

        <section className="panel list-panel">
          <div className="list-heading">
            <div>
              <p className="eyebrow">Pipeline</p>
              <h2>Clients</h2>
            </div>
            <button className="ghost" onClick={loadClients} disabled={loading}>{loading ? 'Loading…' : 'Reload'}</button>
          </div>

          <div className="client-list">
            {clients.map((client) => (
              <article className="client-card" key={client.id}>
                <div className="client-topline">
                  <div>
                    <h3>{client.name}</h3>
                    <p>{client.businessType || 'Business type missing'} · {client.serviceArea || client.city || 'Area missing'}</p>
                  </div>
                  <span className={`status ${client.status}`}>{STATUS_LABELS[client.status]}</span>
                </div>

                <div className="meta-row">
                  {client.website ? <a href={client.website} target="_blank" rel="noreferrer">Website</a> : <span>No website</span>}
                  <span>{client.photos.length} photo{client.photos.length === 1 ? '' : 's'}</span>
                  <span>Updated {formatDate(client.updatedAt)}</span>
                </div>

                {client.notes ? <p className="notes">{client.notes}</p> : null}

                <div className="actions">
                  <button onClick={() => setStatus(client, 'queued')}>Queue</button>
                  <button onClick={() => setStatus(client, 'generating')}>Generating</button>
                  <button onClick={() => setStatus(client, 'generated')}>Generated</button>
                  <button className="danger" onClick={() => removeClient(client)}>Delete</button>
                </div>
              </article>
            ))}

            {!loading && !clients.length ? (
              <div className="empty-state">
                <h3>No clients yet.</h3>
                <p>Add the first business on the left. Client data will be saved in the Pi runtime store, not committed to GitHub.</p>
              </div>
            ) : null}
          </div>
        </section>
      </section>
    </main>
  );
}
