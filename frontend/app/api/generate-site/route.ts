import { spawn } from 'child_process';
import path from 'path';
import { NextResponse } from 'next/server';
import { readClients, updateClient } from '../../../lib/client-store';

type ClientRecord = Awaited<ReturnType<typeof readClients>>[number];

function repoRoot() {
  return path.resolve(process.cwd(), '..');
}

function toBusiness(client: ClientRecord) {
  return {
    name: client.name,
    business_type: client.businessType,
    city: client.city,
    service_area: client.serviceArea || client.city,
    website: client.website,
    email: client.email,
    phone: client.phone,
    notes: client.notes,
    photos: client.photos,
  };
}

function runGenerator(business: unknown) {
  const script = `
import json
import sys
from backend.app.services.site_generator import generate_site
business = json.load(sys.stdin)
site = generate_site(business)
print(json.dumps({"slug": site.slug, "path": str(site.path), "refined_with_codex": site.refined_with_codex}))
`;

  return new Promise<{ path?: string }>((resolve, reject) => {
    const child = spawn('python3', ['-c', script], {
      cwd: repoRoot(),
      env: process.env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr || stdout || `Generator exited with code ${code}`));
        return;
      }
      const lines = stdout.trim().split(/\n/).filter(Boolean);
      resolve(JSON.parse(lines[lines.length - 1] || '{}'));
    });
    child.stdin.write(JSON.stringify(business));
    child.stdin.end();
  });
}

function requestIds(body: { id?: unknown; ids?: unknown }) {
  const ids = Array.isArray(body.ids) ? body.ids : body.id ? [body.id] : [];
  return [...new Set(ids.map((id) => String(id || '').trim()).filter(Boolean))];
}

export async function POST(request: Request) {
  const body = await request.json();
  const ids = requestIds(body);

  if (!ids.length) {
    return NextResponse.json({ error: 'No leads selected.' }, { status: 400 });
  }

  const clients = await readClients();
  const selected = ids.map((id) => clients.find((item) => item.id === id)).filter(Boolean) as ClientRecord[];

  if (!selected.length) {
    return NextResponse.json({ error: 'Selected leads were not found.' }, { status: 404 });
  }

  for (const client of selected) {
    await updateClient(client.id, { status: 'queued', error: '', generatedSitePath: client.generatedSitePath || '' });
  }

  const results = [];
  for (const client of selected) {
    await updateClient(client.id, { status: 'generating', error: '', generatedSitePath: '' });
    try {
      const result = await runGenerator(toBusiness(client));
      const updated = await updateClient(client.id, { status: 'generated', error: '', generatedSitePath: result.path || '' });
      results.push({ id: client.id, ok: true, client: updated, result });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Site generation failed.';
      const updated = await updateClient(client.id, { status: 'error', error: message });
      results.push({ id: client.id, ok: false, client: updated, error: message });
    }
  }

  const latest = await readClients();
  const failed = results.filter((item) => !item.ok);
  return NextResponse.json({ clients: latest, results, failed: failed.length }, { status: failed.length ? 207 : 200 });
}
