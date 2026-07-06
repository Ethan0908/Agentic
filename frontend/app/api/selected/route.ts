import { promises as fs } from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';
import { readClients, updateClient } from '../../../lib/client-store';

type Row = Record<string, any>;
const STORE = process.env.CLIENT_DATA_FILE || path.resolve(process.cwd(), '..', '.runtime', 'clients.json');

function idsFrom(value: unknown) {
  return Array.isArray(value) ? [...new Set(value.map((id) => String(id || '').trim()).filter(Boolean))] : [];
}

async function saveRows(rows: Row[]) {
  await fs.mkdir(path.dirname(STORE), { recursive: true });
  await fs.writeFile(STORE, JSON.stringify({ version: 1, clients: rows }, null, 2) + '\n', 'utf-8');
}

export async function POST(request: Request) {
  const body = await request.json();
  const action = String(body.action || '').trim();
  const ids = idsFrom(body.ids);

  if (!ids.length) {
    return NextResponse.json({ error: 'No leads selected.' }, { status: 400 });
  }

  if (action === 'email') {
    for (const id of ids) await updateClient(id, { status: 'emailed' });
  } else if (action === 'clear-site') {
    const rows = (await readClients()) as Row[];
    for (const row of rows) {
      if (!ids.includes(row.id)) continue;
      row.generatedRepoUrl = '';
      row.githubUrl = '';
      row.repoUrl = '';
      row.vercelUrl = '';
      row.deploymentUrl = '';
      row.liveUrl = '';
      row.generatedSitePath = '';
      row.status = 'lead';
      row.error = '';
      row.siteDeletedAt = new Date().toISOString();
      row.updatedAt = new Date().toISOString();
    }
    await saveRows(rows);
  } else {
    return NextResponse.json({ error: 'Unknown selected action.' }, { status: 400 });
  }

  return NextResponse.json({ clients: await readClients() });
}
