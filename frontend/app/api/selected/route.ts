import { NextResponse } from 'next/server';
import { deleteClient, readClients, updateClient } from '../../../lib/client-store';

function idsFrom(value: unknown) {
  return Array.isArray(value) ? [...new Set(value.map((id) => String(id || '').trim()).filter(Boolean))] : [];
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
  } else if (action === 'delete') {
    for (const id of ids) await deleteClient(id);
  } else {
    return NextResponse.json({ error: 'Unknown selected action.' }, { status: 400 });
  }

  return NextResponse.json({ clients: await readClients() });
}
