import { spawn } from 'child_process';
import path from 'path';
import { NextResponse } from 'next/server';
import { readClients, updateClient } from '../../../../../lib/client-store';

type RouteContext = {
  params: Promise<{ id: string }>;
};

type GenerateResult = {
  slug?: string;
  path?: string;
  refined_with_codex?: boolean;
};

function repoRoot() {
  return path.resolve(process.cwd(), '..');
}

function clientToBusiness(client: Awaited<ReturnType<typeof readClients>>[number]) {
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

function runGenerator(business: unknown): Promise<GenerateResult> {
  const script = `
import json
import sys
from backend.app.services.site_generator import generate_site

business = json.load(sys.stdin)
site = generate_site(business)
print(json.dumps({
    "slug": site.slug,
    "path": str(site.path),
    "refined_with_codex": site.refined_with_codex,
}))
`;

  return new Promise((resolve, reject) => {
    const child = spawn('python3', ['-c', script], {
      cwd: repoRoot(),
      env: process.env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr || stdout || `Generator exited with code ${code}`));
        return;
      }
      try {
        const lines = stdout.trim().split(/\n/).filter(Boolean);
        resolve(JSON.parse(lines[lines.length - 1] || '{}'));
      } catch (error) {
        reject(new Error(`Generator finished but returned invalid JSON: ${stdout}`));
      }
    });

    child.stdin.write(JSON.stringify(business));
    child.stdin.end();
  });
}

export async function POST(_request: Request, context: RouteContext) {
  const { id } = await context.params;
  const clients = await readClients();
  const client = clients.find((item) => item.id === id);

  if (!client) {
    return NextResponse.json({ error: 'Client not found.' }, { status: 404 });
  }

  await updateClient(id, { status: 'generating', error: '', generatedSitePath: '' });

  try {
    const result = await runGenerator(clientToBusiness(client));
    const updated = await updateClient(id, {
      status: 'generated',
      error: '',
      generatedSitePath: result.path || '',
    });
    return NextResponse.json({ client: updated, result });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Site generation failed.';
    const updated = await updateClient(id, { status: 'error', error: message });
    return NextResponse.json({ error: message, client: updated }, { status: 500 });
  }
}
