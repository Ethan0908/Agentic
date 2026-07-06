import { NextResponse } from 'next/server';
import { createClient, readClients } from '../../../lib/client-store';

export async function GET() {
  const clients = await readClients();
  return NextResponse.json({ clients });
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const client = await createClient(body);
    return NextResponse.json({ client }, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unable to create client.' },
      { status: 400 },
    );
  }
}
