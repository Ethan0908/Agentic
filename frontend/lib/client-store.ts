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
  createdAt: string;
  updatedAt: string;
};

type ClientInput = Partial<Omit<ClientRecord, 'id' | 'createdAt' | 'updatedAt'>> & {
  name?: string;
};

type StoreShape = {
  version: 1;
  clients: ClientRecord[];
};

const DEFAULT_STORE = path.resolve(process.cwd(), '..', '.runtime', 'clients.json');
const STORE_FILE = process.env.CLIENT_DATA_FILE || DEFAULT_STORE;

function cleanText(value: unknown): string {
  return String(value || '').trim();
}

function cleanPhotos(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => cleanText(item))
    .filter((item) => /^https?:\/\//i.test(item))
    .slice(0, 8);
}

function newId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

async function ensureStore(): Promise<void> {
  await fs.mkdir(path.dirname(STORE_FILE), { recursive: true });
  try {
    await fs.access(STORE_FILE);
  } catch {
    await fs.writeFile(STORE_FILE, JSON.stringify({ version: 1, clients: [] }, null, 2) + '\n', 'utf-8');
  }
}

export async function readClients(): Promise<ClientRecord[]> {
  await ensureStore();
  const raw = await fs.readFile(STORE_FILE, 'utf-8');
  const parsed = JSON.parse(raw) as StoreShape;
  return Array.isArray(parsed.clients) ? parsed.clients : [];
}

async function writeClients(clients: ClientRecord[]): Promise<void> {
  await ensureStore();
  const payload: StoreShape = { version: 1, clients };
  await fs.writeFile(STORE_FILE, JSON.stringify(payload, null, 2) + '\n', 'utf-8');
}

export async function createClient(input: ClientInput): Promise<ClientRecord> {
  const name = cleanText(input.name);
  if (!name) {
    throw new Error('Client name is required.');
  }

  const now = new Date().toISOString();
  const client: ClientRecord = {
    id: newId(),
    name,
    businessType: cleanText(input.businessType),
    city: cleanText(input.city),
    serviceArea: cleanText(input.serviceArea),
    website: cleanText(input.website),
    email: cleanText(input.email),
    phone: cleanText(input.phone),
    notes: cleanText(input.notes),
    photos: cleanPhotos(input.photos),
    status: input.status || 'lead',
    createdAt: now,
    updatedAt: now,
  };

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
  const updated: ClientRecord = {
    ...existing,
    name: input.name === undefined ? existing.name : cleanText(input.name),
    businessType: input.businessType === undefined ? existing.businessType : cleanText(input.businessType),
    city: input.city === undefined ? existing.city : cleanText(input.city),
    serviceArea: input.serviceArea === undefined ? existing.serviceArea : cleanText(input.serviceArea),
    website: input.website === undefined ? existing.website : cleanText(input.website),
    email: input.email === undefined ? existing.email : cleanText(input.email),
    phone: input.phone === undefined ? existing.phone : cleanText(input.phone),
    notes: input.notes === undefined ? existing.notes : cleanText(input.notes),
    photos: input.photos === undefined ? existing.photos : cleanPhotos(input.photos),
    status: input.status || existing.status,
    error: input.error === undefined ? existing.error : cleanText(input.error),
    generatedSitePath: input.generatedSitePath === undefined ? existing.generatedSitePath : cleanText(input.generatedSitePath),
    updatedAt: new Date().toISOString(),
  };

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
