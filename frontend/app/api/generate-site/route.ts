import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';
import { readClients, updateClient } from '../../../lib/client-store';
import { publishToGithub, publishToVercel } from '../../../lib/site-publisher';

type ClientRecord = Awaited<ReturnType<typeof readClients>>[number];
type GenResult = { slug?: string; path?: string; design_system?: string; refined_with_codex?: boolean };

type BusinessInput = {
  name: string;
  business_type: string;
  city: string;
  service_area: string;
  website: string;
  email: string;
  phone: string;
  notes: string;
  photos: unknown;
  address?: string;
  rating?: string;
  review_count?: string;
  content_angles?: string[];
  visitor_questions?: string[];
  proof_points?: string[];
};

function repoRoot() { return path.resolve(process.cwd(), '..'); }
function repoName(name: string) { return `site-${name}`.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 90) || 'site-generated'; }
async function removeLocalSite(sitePath: string) { await fs.rm(sitePath, { recursive: true, force: true }).catch(() => undefined); }

function codexReasoningEffort() {
  const value = String(process.env.CODEX_REASONING_EFFORT || 'high').trim().toLowerCase().replace(/["']/g, '');
  return ['low', 'medium', 'high'].includes(value) ? value : 'high';
}

function extractRating(text: string) {
  return text.match(/(?<!\d)([0-5](?:\.\d{1,2})?)\s*(?:\/\s*5\s*)?(?:google\s*)?rating\b/i)?.[1] || '';
}

function extractReviewCount(text: string) {
  return (text.match(/\b([\d,]{1,7})\s*(?:google\s*)?reviews?\b/i)?.[1] || '').replace(/,/g, '');
}

function extractAddress(text: string) {
  const streetTerms = /\b(street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|court|ct|place|pl|parkway|pkwy|highway|hwy|way|suite|ste)\b|#/i;
  const candidates = text.split(/[•|\n]/).map((item) => item.trim()).filter(Boolean).reverse();
  const exact = candidates.find((candidate) => /\d/.test(candidate) && streetTerms.test(candidate));
  if (exact) return exact.replace(/^[,\s]+|[,\s]+$/g, '');
  return text.match(/\b\d{1,6}\s+[A-Za-z0-9 .#'-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl)[^•\n|]*/i)?.[0]?.trim() || '';
}

function contentAnglesFor(businessType: string, address: string, rating: string, reviewCount: string, phone: string, website: string) {
  const lowered = businessType.toLowerCase();
  const angles: string[] = [];
  if (/dentist|dental|clinic|medical|therapy|health/.test(lowered)) {
    angles.push('appointment and booking questions', 'location and arrival details', 'care categories to ask the office about');
  } else if (/plumb|hvac|electric|repair|contractor|roof/.test(lowered)) {
    angles.push('problem type and urgency', 'service-area expectations', 'what to ask before booking');
  } else if (/restaurant|bakery|barber|salon|spa/.test(lowered)) {
    angles.push('visit intent and location', 'booking or ordering path', 'category expectations without inventing menu items or prices');
  } else {
    angles.push('what the business does', 'who the visitor is likely to be', 'how to take the next step');
  }
  if (address && !angles.includes('location and arrival details')) angles.push('location and arrival details');
  if (rating || reviewCount) angles.push('public listing proof without exaggerating claims');
  if (phone) angles.push('phone-first contact path');
  else if (website) angles.push('website-first conversion path');
  return [...new Set(angles)].slice(0, 6);
}

function visitorQuestionsFor(businessType: string, address: string, phone: string, website: string) {
  const label = businessType.toLowerCase() || 'business';
  const questions = [`What should I know before contacting this ${label}?`, 'What facts are available from the listing?'];
  if (address) questions.push('Where is it located and how should I plan my visit?');
  if (phone) questions.push('What should I ask when I call?');
  if (website) questions.push('What can I confirm on the official website?');
  return questions.slice(0, 5);
}

function toBusiness(client: ClientRecord): BusinessInput {
  const notes = String(client.notes || '');
  const businessType = String(client.businessType || '');
  const website = String(client.website || '');
  const phone = String(client.phone || '');
  const rating = extractRating(notes);
  const reviewCount = extractReviewCount(notes);
  const address = extractAddress(notes);
  const proofPoints = [
    rating ? `${rating} Google rating` : '',
    reviewCount ? `${reviewCount} Google reviews` : '',
    address ? `Listed address: ${address}` : '',
  ].filter(Boolean);

  return {
    name: client.name,
    business_type: businessType,
    city: client.city,
    service_area: client.serviceArea || client.city,
    website,
    email: client.email,
    phone,
    notes,
    photos: client.photos,
    address,
    rating,
    review_count: reviewCount,
    content_angles: contentAnglesFor(businessType, address, rating, reviewCount, phone, website),
    visitor_questions: visitorQuestionsFor(businessType, address, phone, website),
    proof_points: proofPoints,
  };
}

function runGenerator(business: unknown): Promise<GenResult> {
  const script = `
import json
import sys
from backend.app.services.site_generator import generate_site
business = json.load(sys.stdin)
site = generate_site(business, refine_with_codex=True, refine_with_claude=False)
print(json.dumps({"slug": site.slug, "path": str(site.path), "design_system": site.design_system, "refined_with_codex": site.refined_with_codex}))
`;
  return new Promise((resolve, reject) => {
    const env = { ...process.env, CODEX_REASONING_EFFORT: codexReasoningEffort() };
    const child = spawn('python3', ['-c', script], { cwd: repoRoot(), env, stdio: ['pipe', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code !== 0) { reject(new Error(stderr || stdout || `Generator exited with code ${code}`)); return; }
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
  if (!ids.length) return NextResponse.json({ error: 'No leads selected.' }, { status: 400 });

  const clients = await readClients();
  const selected = ids.map((id) => clients.find((item) => item.id === id)).filter(Boolean) as ClientRecord[];
  if (!selected.length) return NextResponse.json({ error: 'Selected leads were not found.' }, { status: 404 });

  for (const client of selected) await updateClient(client.id, { status: 'queued', error: '', generatedSitePath: '' });

  const results = [];
  for (const client of selected) {
    let localPath = '';
    let generatedRepoUrl = '';
    let vercelUrl = '';
    await updateClient(client.id, { status: 'generating', error: '', generatedSitePath: '' });
    try {
      const result = await runGenerator(toBusiness(client));
      if (!result.path) throw new Error('Generator did not return a site path.');
      if (!result.refined_with_codex) throw new Error('Codex refinement did not run; refusing to publish scaffold-quality site.');
      localPath = result.path;
      const publishInput = { sitePath: result.path, repoName: repoName(client.name), displayName: client.name };

      generatedRepoUrl = await publishToGithub(publishInput);
      await updateClient(client.id, { status: 'generating', error: 'High-quality Codex site published to GitHub; Vercel pending.', generatedSitePath: '', generatedRepoUrl } as any);

      vercelUrl = await publishToVercel(publishInput);
      await updateClient(client.id, { status: 'generating', error: 'GitHub and Vercel published; cleaning local workspace.', generatedSitePath: '', generatedRepoUrl, vercelUrl } as any);

      await removeLocalSite(result.path);
      const updated = await updateClient(client.id, { status: 'generated', error: '', generatedSitePath: '', generatedRepoUrl, vercelUrl } as any);
      results.push({ id: client.id, ok: true, client: updated, result: { slug: result.slug, design_system: result.design_system, refined_with_codex: result.refined_with_codex, generatedRepoUrl, vercelUrl } });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Site generation or publish failed.';
      const updated = await updateClient(client.id, { status: 'error', error: message, generatedSitePath: localPath, generatedRepoUrl, vercelUrl } as any);
      results.push({ id: client.id, ok: false, client: updated, error: message, generatedRepoUrl, vercelUrl });
    }
  }

  const latest = await readClients();
  const failed = results.filter((item) => !item.ok);
  return NextResponse.json({ clients: latest, results, failed: failed.length }, { status: failed.length ? 207 : 200 });
}
