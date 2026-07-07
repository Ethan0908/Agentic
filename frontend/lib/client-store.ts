import { promises as fs } from 'fs';
import path from 'path';

export type ClientStatus = 'lead' | 'queued' | 'generating' | 'generated' | 'emailed' | 'error';

export type ClientRecord = {
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
  generatedRepoUrl?: string;
  githubUrl?: string;
  repoUrl?: string;
  vercelUrl?: string;
  deploymentUrl?: string;
  liveUrl?: string;
  createdAt: string;
  updatedAt: string;
};

type ClientInput = Partial<Omit<ClientRecord, 'id' | 'createdAt' | 'updatedAt'>> & { name?: string };
type StoreShape = { version: 1; clients: ClientRecord[] };

const DEFAULT_STORE = path.resolve(process.cwd(), '..', '.runtime', 'clients.json');
const STORE_FILE = process.env.CLIENT_DATA_FILE || DEFAULT_STORE;

function cleanText(value: unknown): string { return String(value || '').trim(); }

function safePhotoUrl(value: unknown): string {
  const url = cleanText(value);
  if (!/^https?:\/\//i.test(url)) return '';
  try {
    const parsed = new URL(url);
    if (parsed.searchParams.has('key')) return '';
    if (parsed.hostname === 'places.googleapis.com' && parsed.pathname.includes('/media')) return '';
    return url;
  } catch { return ''; }
}

function cleanPhotos(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map(safePhotoUrl).filter(Boolean).slice(0, 8);
}

function newId() { return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`; }

function normalizeClient(row: any): ClientRecord {
  return {
    ...row,
    id: cleanText(row.id) || newId(),
    name: cleanText(row.name),
    businessType: cleanText(row.businessType),
    city: cleanText(row.city),
    serviceArea: cleanText(row.serviceArea),
    website: cleanText(row.website),
    email: cleanText(row.email),
    phone: cleanText(row.phone),
    notes: cleanText(row.notes),
    photos: cleanPhotos(row.photos),
    status: row.status || 'lead',
    error: cleanText(row.error),
    generatedSitePath: cleanText(row.generatedSitePath),
    generatedRepoUrl: cleanText(row.generatedRepoUrl),
    githubUrl: cleanText(row.githubUrl),
    repoUrl: cleanText(row.repoUrl),
    vercelUrl: cleanText(row.vercelUrl),
    deploymentUrl: cleanText(row.deploymentUrl),
    liveUrl: cleanText(row.liveUrl),
    createdAt: cleanText(row.createdAt) || new Date().toISOString(),
    updatedAt: cleanText(row.updatedAt) || new Date().toISOString(),
  };
}

async function ensureStore(): Promise<void> {
  await fs.mkdir(path.dirname(STORE_FILE), { recursive: true });
  try { await fs.access(STORE_FILE); } catch { await fs.writeFile(STORE_FILE, JSON.stringify({ version: 1, clients: [] }, null, 2) + '\n', 'utf-8'); }
}

export async function readClients(): Promise<ClientRecord[]> {
  await ensureStore();
  const raw = await fs.readFile(STORE_FILE, 'utf-8');
  const parsed = JSON.parse(raw) as StoreShape;
  return Array.isArray(parsed.clients) ? parsed.clients.map(normalizeClient) : [];
}

async function writeClients(clients: ClientRecord[]): Promise<void> {
  await ensureStore();
  await fs.writeFile(STORE_FILE, JSON.stringify({ version: 1, clients: clients.map(normalizeClient) }, null, 2) + '\n', 'utf-8');
}

export async function createClient(input: ClientInput): Promise<ClientRecord> {
  const name = cleanText(input.name);
  if (!name) throw new Error('Client name is required.');
  const now = new Date().toISOString();
  const client = normalizeClient({ ...input, id: newId(), name, status: input.status || 'lead', createdAt: now, updatedAt: now });
  const clients = await readClients();
  clients.unshift(client);
  await writeClients(clients);
  return client;
}

export async function updateClient(id: string, input: ClientInput): Promise<ClientRecord | null> {
  const clients = await readClients();
  const index = clients.findIndex((client) => client.id === id);
  if (index === -1) return null;
  const existing = clients[index];
  const updated = normalizeClient({
    ...existing,
    ...input,
    photos: input.photos === undefined ? existing.photos : input.photos,
    status: input.status || existing.status,
    error: input.error === undefined ? existing.error : input.error,
    generatedSitePath: input.generatedSitePath === undefined ? existing.generatedSitePath : input.generatedSitePath,
    generatedRepoUrl: input.generatedRepoUrl === undefined ? existing.generatedRepoUrl : input.generatedRepoUrl,
    githubUrl: input.githubUrl === undefined ? existing.githubUrl : input.githubUrl,
    repoUrl: input.repoUrl === undefined ? existing.repoUrl : input.repoUrl,
    vercelUrl: input.vercelUrl === undefined ? existing.vercelUrl : input.vercelUrl,
    deploymentUrl: input.deploymentUrl === undefined ? existing.deploymentUrl : input.deploymentUrl,
    liveUrl: input.liveUrl === undefined ? existing.liveUrl : input.liveUrl,
    updatedAt: new Date().toISOString(),
  });
  clients[index] = updated;
  await writeClients(clients);
  return updated;
}

export async function deleteClient(id: string): Promise<boolean> {
  const clients = await readClients();
  const next = clients.filter((client) => client.id !== id);
  if (next.length === clients.length) return false;
  await writeClients(next);
  return true;
}
