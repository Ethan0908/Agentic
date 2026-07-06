import { execFile } from 'child_process';
import { NextResponse } from 'next/server';
import { createClient } from '../../../lib/client-store';

type RawLead = {
  name?: string;
  businessName?: string;
  business_type?: string;
  businessType?: string;
  city?: string;
  service_area?: string;
  serviceArea?: string;
  website?: string;
  url?: string;
  email?: string;
  phone?: string;
  notes?: string;
  photos?: string[];
};

function splitCommand(command: string) {
  return command.match(/(?:[^\s"]+|"[^"]*")+/g)?.map((part) => part.replace(/^"|"$/g, '')) || [];
}

function normalizeLead(lead: RawLead, fallbackNotes: string) {
  return {
    name: String(lead.name || lead.businessName || '').trim(),
    businessType: String(lead.businessType || lead.business_type || '').trim(),
    city: String(lead.city || '').trim(),
    serviceArea: String(lead.serviceArea || lead.service_area || lead.city || '').trim(),
    website: String(lead.website || lead.url || '').trim(),
    email: String(lead.email || '').trim(),
    phone: String(lead.phone || '').trim(),
    notes: String(lead.notes || fallbackNotes || '').trim(),
    photos: Array.isArray(lead.photos) ? lead.photos : [],
    status: 'lead' as const,
  };
}

function runFinder(command: string, query: string, location: string, limit: string): Promise<RawLead[]> {
  const parts = splitCommand(command);
  const executable = parts[0];
  const args = parts.slice(1);

  return new Promise((resolve, reject) => {
    if (!executable) {
      reject(new Error('LEAD_FINDER_COMMAND is empty.'));
      return;
    }

    const child = execFile(executable, args, {
      env: {
        ...process.env,
        LEAD_FINDER_QUERY: query,
        LEAD_FINDER_LOCATION: location,
        LEAD_FINDER_LIMIT: limit,
      },
      timeout: 180000,
      maxBuffer: 1024 * 1024 * 20,
    }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(stderr || error.message));
        return;
      }
      try {
        const parsed = JSON.parse(stdout || '[]');
        const leads = Array.isArray(parsed) ? parsed : parsed.leads;
        resolve(Array.isArray(leads) ? leads : []);
      } catch {
        reject(new Error(`Lead finder returned invalid JSON: ${stdout.slice(0, 600)}`));
      }
    });

    child.stdin?.end();
  });
}

export async function POST(request: Request) {
  const body = await request.json();
  const query = String(body.query || '').trim();
  const location = String(body.location || '').trim();
  const limit = String(body.limit || '20').trim();
  const command = process.env.LEAD_FINDER_COMMAND || '';

  if (!command) {
    return NextResponse.json({
      error: 'LEAD_FINDER_COMMAND is not set. Set it to your existing lead-finder script command, which should print JSON leads.',
    }, { status: 500 });
  }

  const rawLeads = await runFinder(command, query, location, limit);
  const created = [];
  for (const rawLead of rawLeads) {
    const lead = normalizeLead(rawLead, `${query}${location ? ` in ${location}` : ''}`);
    if (!lead.name) continue;
    created.push(await createClient(lead));
  }

  return NextResponse.json({ created, count: created.length });
}
