import { promises as fs } from 'fs';
import path from 'path';
import { spawn } from 'child_process';

export type PublishInput = {
  sitePath: string;
  repoName: string;
  displayName: string;
};

const SKIP_DIRS = new Set(['.git', '.next', 'node_modules']);

function run(command: string, args: string[], cwd: string) {
  return new Promise<{ stdout: string; stderr: string }>((resolve, reject) => {
    const child = spawn(command, args, { cwd, env: process.env, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', reject);
    child.on('close', (code) => code === 0 ? resolve({ stdout, stderr }) : reject(new Error(stderr || stdout || `${command} exited with ${code}`)));
  });
}

async function walk(root: string, dir = root): Promise<string[]> {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    if (entry.isDirectory() && SKIP_DIRS.has(entry.name)) continue;
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
  if (!response.ok && response.status !== 404 && response.status !== 422) {
    throw new Error(await response.text());
  }
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

export async function publishToVercel(input: PublishInput) {
  const token = process.env.VERCEL_TOKEN || '';
  if (!token) throw new Error('Set VERCEL_TOKEN to deploy generated sites.');
  const args = ['-y', 'vercel@latest', 'deploy', '--prod', '--yes', '--token', token, '--name', input.repoName];
  const result = await run('npx', args, input.sitePath);
  const pieces = `${result.stdout}\n${result.stderr}`.split(/\s+/);
  const url = pieces.find((part) => /^https:\/\/[^\s]+\.vercel\.app\/?$/.test(part));
  if (!url) throw new Error('Vercel did not return a deployment URL.');
  return url.replace(/\/$/, '');
}
