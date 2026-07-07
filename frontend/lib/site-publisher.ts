import { promises as fs } from 'fs';
import path from 'path';

export type PublishInput = {
  sitePath: string;
  repoName: string;
  displayName: string;
};

const SKIP_DIRS = new Set(['.git', '.next', 'node_modules']);
const SKIP_FILES = new Set(['package-lock.json']);

async function walk(root: string, dir = root): Promise<string[]> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    if (entry.isDirectory() && SKIP_DIRS.has(entry.name)) continue;
    if (entry.isFile() && SKIP_FILES.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...await walk(root, full));
    if (entry.isFile()) files.push(path.relative(root, full));
  }
  return files;
}

function ghHeaders(token: string) {
  return { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'Content-Type': 'application/json' };
}

async function githubRequest(url: string, init: RequestInit) {
  const response = await fetch(url, init);
  if (!response.ok && response.status !== 404 && response.status !== 422) throw new Error(await response.text());
  return response;
}

export async function publishToGithub(input: PublishInput) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
  const owner = process.env.GITHUB_OWNER || process.env.GH_OWNER || '';
  if (!token || !owner) throw new Error('Set GITHUB_TOKEN and GITHUB_OWNER to publish generated sites.');

  await githubRequest('https://api.github.com/user/repos', {
    method: 'POST',
    headers: ghHeaders(token),
    body: JSON.stringify({ name: input.repoName, private: false, auto_init: true }),
  });

  const files = await walk(input.sitePath);
  for (const file of files) {
    const absolute = path.join(input.sitePath, file);
    const content = await fs.readFile(absolute);
    const apiPath = encodeURIComponent(file).replace(/%2F/g, '/');
    const getUrl = `https://api.github.com/repos/${owner}/${input.repoName}/contents/${apiPath}`;
    const current = await fetch(getUrl, { headers: ghHeaders(token) });
    const existing = current.ok ? await current.json() : null;
    await githubRequest(getUrl, {
      method: 'PUT',
      headers: ghHeaders(token),
      body: JSON.stringify({ message: `Publish ${input.displayName}`, content: content.toString('base64'), sha: existing?.sha }),
    });
  }

  return `https://github.com/${owner}/${input.repoName}`;
}

function vercelHeaders(token: string) {
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
}

function vercelApi(pathname: string) {
  const url = new URL(`https://api.vercel.com${pathname}`);
  if (process.env.VERCEL_TEAM_ID) url.searchParams.set('teamId', process.env.VERCEL_TEAM_ID);
  if (process.env.VERCEL_TEAM_SLUG) url.searchParams.set('slug', process.env.VERCEL_TEAM_SLUG);
  return url;
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function vercelJson(url: URL, init: RequestInit, token: string) {
  const response = await fetch(url, { ...init, headers: { ...vercelHeaders(token), ...(init.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error?.message || JSON.stringify(data).slice(0, 1200));
  return data;
}

async function waitForReady(id: string, token: string) {
  for (let attempt = 0; attempt < 90; attempt += 1) {
    const data = await vercelJson(vercelApi(`/v13/deployments/${encodeURIComponent(id)}`), { method: 'GET' }, token);
    if (data.readyState === 'READY') return data;
    if (data.readyState === 'ERROR' || data.readyState === 'CANCELED') throw new Error(data.errorMessage || `Vercel deployment ${data.readyState}.`);
    await sleep(3000);
  }
  throw new Error('Timed out waiting for Vercel deployment to become READY.');
}

async function assignAlias(id: string, alias: string, token: string) {
  const data = await vercelJson(vercelApi(`/v2/deployments/${encodeURIComponent(id)}/aliases`), {
    method: 'POST',
    body: JSON.stringify({ alias }),
  }, token);
  return data.alias || alias;
}

export async function publishToVercel(input: PublishInput) {
  const token = process.env.VERCEL_TOKEN || '';
  if (!token) throw new Error('Set VERCEL_TOKEN to deploy generated sites.');

  const files = await walk(input.sitePath);
  const payloadFiles = [];
  for (const file of files) {
    const content = await fs.readFile(path.join(input.sitePath, file));
    payloadFiles.push({ file, data: content.toString('base64'), encoding: 'base64' });
  }

  const deployment = await vercelJson(vercelApi('/v13/deployments'), {
    method: 'POST',
    body: JSON.stringify({
      name: input.repoName,
      project: input.repoName,
      target: 'production',
      files: payloadFiles,
      projectSettings: {
        framework: 'nextjs',
        buildCommand: 'npm run build',
        installCommand: 'npm install',
        outputDirectory: '.next',
      },
    }),
  }, token);

  const id = deployment.id || deployment.uid;
  if (!id) throw new Error(`Vercel deployment did not return an id: ${JSON.stringify(deployment).slice(0, 1200)}`);
  await waitForReady(id, token);
  const alias = `${input.repoName}.vercel.app`;
  const assigned = await assignAlias(id, alias, token);
  return `https://${assigned}`;
}
