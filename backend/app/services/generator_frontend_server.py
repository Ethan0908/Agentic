from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .site_generator import normalize_business_profile, slugify

REPO_ROOT = Path(__file__).resolve().parents[3]
JOBS_DIR = REPO_ROOT / ".generator_jobs"
DEFAULT_LEAD = REPO_ROOT / "leads" / "example-plumber.json"

JOBS: dict[str, dict[str, Any]] = {}
JOBS_LOCK = threading.Lock()
PREVIEW_PROCESSES: dict[str, subprocess.Popen[str]] = {}


def now() -> str:
    return time.strftime("%H:%M:%S")


def lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "localhost"


def free_port(start: int = 3100) -> int:
    for port in range(start, start + 200):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No free preview port found from 3100-3299.")


def append_log(job_id: str, line: str) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return
        job.setdefault("logs", []).append(f"[{now()}] {line.rstrip()}")
        job["logs"] = job["logs"][-500:]


def set_job(job_id: str, **values: Any) -> None:
    with JOBS_LOCK:
        JOBS[job_id].update(values)


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw)


def send_json(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json; charset=utf-8")
    handler.send_header("access-control-allow-origin", "*")
    handler.send_header("content-length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def send_html(handler: BaseHTTPRequestHandler, html: str, status: int = 200) -> None:
    body = html.encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "text/html; charset=utf-8")
    handler.send_header("content-length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def default_profile() -> dict[str, Any]:
    if DEFAULT_LEAD.exists():
        return json.loads(DEFAULT_LEAD.read_text(encoding="utf-8"))
    return {
        "name": "NYC Emergency Plumbing",
        "business_type": "emergency plumbing",
        "city": "New York",
        "service_area": "Manhattan, Brooklyn, and Queens",
        "primary_cta": "Request emergency service",
        "secondary_cta": "See plumbing services",
        "services": [
            {"title": "Drain clearing", "description": "Clear blocked drains with a practical diagnosis before work starts."},
            {"title": "Leak repair", "description": "Find the source of the leak and explain the next step clearly."},
            {"title": "Sewer service", "description": "Understand the source of the blockage and the practical next step."}
        ]
    }


def run_and_stream(job_id: str, command: list[str], cwd: Path) -> int:
    append_log(job_id, "▶ " + " ".join(command[:4]) + " ...")
    append_log(job_id, f"cwd: {cwd}")
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        append_log(job_id, line)
    return process.wait()


def stream_preview_logs(job_id: str, process: subprocess.Popen[str]) -> None:
    if process.stdout is None:
        return
    for line in process.stdout:
        append_log(job_id, "preview: " + line)


def start_preview(job_id: str, site_path: Path) -> dict[str, Any]:
    port = free_port()
    command = ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", str(port)]
    process = subprocess.Popen(
        command,
        cwd=site_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
        bufsize=1,
    )
    PREVIEW_PROCESSES[job_id] = process
    threading.Thread(target=stream_preview_logs, args=(job_id, process), daemon=True).start()
    return {
        "port": port,
        "localUrl": f"http://localhost:{port}",
        "networkUrl": f"http://{lan_ip()}:{port}",
    }


def generate_worker(job_id: str) -> None:
    with JOBS_LOCK:
        job = JOBS[job_id]
        profile = job["profile"]
        codex_command = job["codexCommand"]
        skip_quality = job["skipQuality"]

    try:
        set_job(job_id, status="running", step="Preparing lead profile")
        normalized = normalize_business_profile(profile)
        slug = slugify(normalized["slug"])
        site_path = REPO_ROOT / "generated_sites" / slug
        job_dir = JOBS_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        profile_file = job_dir / "lead.json"
        profile_file.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        append_log(job_id, f"Business: {normalized['name']}")
        append_log(job_id, f"Slug: {slug}")
        append_log(job_id, f"Codex command: {codex_command}")
        set_job(job_id, slug=slug, sitePath=str(site_path), step="Running Codex scratch generator")

        command = [
            sys.executable,
            "-m",
            "backend.app.services.codex_scratch_generator",
            str(profile_file),
            "--codex-command",
            codex_command,
        ]
        if skip_quality:
            command.append("--skip-quality")
        exit_code = run_and_stream(job_id, command, REPO_ROOT)
        if exit_code != 0:
            set_job(job_id, status="failed", step="Generation failed", exitCode=exit_code)
            append_log(job_id, f"Generation failed with exit code {exit_code}.")
            return

        set_job(job_id, step="Starting preview")
        preview = start_preview(job_id, site_path)
        set_job(job_id, status="complete", step="Preview ready", preview=preview)
        append_log(job_id, f"Preview ready: {preview['networkUrl']}")
    except Exception as exc:
        set_job(job_id, status="failed", step="Exception", error=str(exc))
        append_log(job_id, "ERROR: " + str(exc))


HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Codex Scratch Website Generator</title>
  <style>
    :root { color-scheme: dark; --bg:#0b0f17; --panel:#111827; --panel2:#0f172a; --ink:#f8fafc; --muted:#94a3b8; --line:#263244; --accent:#f59e0b; --good:#22c55e; --bad:#ef4444; }
    * { box-sizing: border-box; }
    body { margin:0; background:linear-gradient(140deg,#070a10,#101827 48%,#111827); color:var(--ink); font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    main { max-width:1280px; margin:0 auto; padding:28px; }
    header { display:flex; justify-content:space-between; gap:18px; align-items:end; margin-bottom:20px; }
    h1 { margin:0; font-size:clamp(2.2rem,5vw,4.8rem); line-height:.9; letter-spacing:-.07em; }
    .sub { color:var(--muted); max-width:760px; line-height:1.55; }
    .grid { display:grid; grid-template-columns:minmax(380px,.85fr) minmax(420px,1fr); gap:18px; align-items:start; }
    .card { background:rgba(17,24,39,.92); border:1px solid var(--line); border-radius:10px; padding:18px; box-shadow:0 24px 80px rgba(0,0,0,.22); }
    label { display:block; margin:0 0 8px; color:#cbd5e1; font-size:.82rem; font-weight:850; text-transform:uppercase; letter-spacing:.12em; }
    textarea,input,select { width:100%; background:#070b12; color:var(--ink); border:1px solid var(--line); border-radius:6px; padding:12px; font:14px ui-monospace,SFMono-Regular,Menlo,monospace; }
    textarea { min-height:560px; resize:vertical; }
    .row { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:12px 0; }
    button,a.button { border:0; border-radius:6px; min-height:46px; padding:0 18px; background:var(--accent); color:#111827; font-weight:950; cursor:pointer; display:inline-flex; align-items:center; justify-content:center; text-decoration:none; }
    button.secondary { background:#1f2937; color:var(--ink); border:1px solid var(--line); }
    button:disabled { opacity:.55; cursor:not-allowed; }
    .status { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:12px; }
    .pill { border:1px solid var(--line); background:#0b1220; padding:8px 10px; border-radius:999px; color:#cbd5e1; font-size:.9rem; }
    .pill.complete { border-color:rgba(34,197,94,.5); color:#86efac; }
    .pill.failed { border-color:rgba(239,68,68,.5); color:#fca5a5; }
    pre { margin:0; white-space:pre-wrap; word-break:break-word; background:#05070b; border:1px solid var(--line); border-radius:8px; padding:14px; min-height:480px; max-height:620px; overflow:auto; color:#dbeafe; font-size:13px; line-height:1.45; }
    .links { display:flex; gap:10px; flex-wrap:wrap; margin:12px 0; }
    @media (max-width: 980px) { .grid { grid-template-columns:1fr; } header { display:block; } textarea { min-height:420px; } }
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Website Generator</h1>
      <p class="sub">Browser-first Codex scratch generation. Paste a lead, click generate, watch logs, then open the generated site preview. This path does not copy site-template.</p>
    </div>
  </header>
  <div class="grid">
    <section class="card">
      <label for="profile">Lead JSON</label>
      <textarea id="profile"></textarea>
      <div class="row">
        <div><label for="codex">Codex command</label><input id="codex" value="/usr/bin/codex" /></div>
        <div><label for="quality">Quality gate</label><select id="quality"><option value="run">Run validator</option><option value="skip">Skip validator</option></select></div>
      </div>
      <div class="links">
        <button id="generate">Generate with Codex</button>
        <button class="secondary" id="loadExample">Reload example</button>
      </div>
    </section>
    <section class="card">
      <div class="status"><span id="status" class="pill">idle</span><span id="step" class="pill">waiting</span><span id="slug" class="pill"></span></div>
      <div class="links" id="previewLinks"></div>
      <label>Live logs</label>
      <pre id="logs"></pre>
    </section>
  </div>
</main>
<script>
const profileEl = document.getElementById('profile');
const logsEl = document.getElementById('logs');
const statusEl = document.getElementById('status');
const stepEl = document.getElementById('step');
const slugEl = document.getElementById('slug');
const linksEl = document.getElementById('previewLinks');
const generateBtn = document.getElementById('generate');
let currentJob = null;
let pollTimer = null;
async function loadExample(){ const r = await fetch('/api/example'); profileEl.value = JSON.stringify(await r.json(), null, 2); }
function setStatus(job){
  statusEl.textContent = job.status || 'unknown'; statusEl.className = 'pill ' + (job.status || '');
  stepEl.textContent = job.step || '';
  slugEl.textContent = job.slug ? 'slug: ' + job.slug : '';
  logsEl.textContent = (job.logs || []).join('\n'); logsEl.scrollTop = logsEl.scrollHeight;
  linksEl.innerHTML = '';
  if(job.preview){
    linksEl.innerHTML = `<a class="button" target="_blank" href="${job.preview.networkUrl}">Open generated site</a><a class="button secondary" target="_blank" href="${job.preview.localUrl}">Local URL</a>`;
  }
  if(job.status === 'complete' || job.status === 'failed'){ generateBtn.disabled = false; clearInterval(pollTimer); }
}
async function poll(){ if(!currentJob) return; const r = await fetch('/api/jobs/' + currentJob); setStatus(await r.json()); }
async function generate(){
  generateBtn.disabled = true; logsEl.textContent = 'Starting...'; linksEl.innerHTML = '';
  let profile; try { profile = JSON.parse(profileEl.value); } catch(e) { alert('Invalid JSON: ' + e.message); generateBtn.disabled = false; return; }
  const body = { profile, codexCommand: document.getElementById('codex').value || 'codex', skipQuality: document.getElementById('quality').value === 'skip' };
  const r = await fetch('/api/generate', { method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(body) });
  const job = await r.json(); currentJob = job.jobId; setStatus(job); pollTimer = setInterval(poll, 1500); poll();
}
document.getElementById('loadExample').onclick = loadExample;
document.getElementById('generate').onclick = generate;
loadExample();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-methods", "GET,POST,OPTIONS")
        self.send_header("access-control-allow-headers", "content-type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            send_html(self, HTML)
            return
        if parsed.path == "/api/example":
            send_json(self, default_profile())
            return
        if parsed.path.startswith("/api/jobs/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
            if not job:
                send_json(self, {"error": "job not found"}, 404)
                return
            send_json(self, job)
            return
        send_json(self, {"error": "not found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/generate":
            send_json(self, {"error": "not found"}, 404)
            return
        try:
            body = read_json_body(self)
            profile = body.get("profile") or default_profile()
            codex_command = body.get("codexCommand") or "/usr/bin/codex"
            job_id = uuid.uuid4().hex[:12]
            with JOBS_LOCK:
                JOBS[job_id] = {
                    "jobId": job_id,
                    "status": "queued",
                    "step": "Queued",
                    "profile": profile,
                    "codexCommand": codex_command,
                    "skipQuality": bool(body.get("skipQuality")),
                    "logs": [],
                    "createdAt": time.time(),
                }
            threading.Thread(target=generate_worker, args=(job_id,), daemon=True).start()
            send_json(self, JOBS[job_id])
        except Exception as exc:
            send_json(self, {"error": str(exc)}, 400)


def main() -> int:
    port = int(os.environ.get("GENERATOR_FRONTEND_PORT", "8090"))
    host = os.environ.get("GENERATOR_FRONTEND_HOST", "0.0.0.0")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Generator frontend local:   http://localhost:{port}")
    print(f"Generator frontend network: http://{lan_ip()}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for process in PREVIEW_PROCESSES.values():
            process.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
