from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from app.core.config import get_settings


IGNORED_DIRS = {".git", ".next", ".vercel", "node_modules", "dist", "build"}
IGNORED_FILES = {".DS_Store"}


class GitHubClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.github_token:
            raise RuntimeError("GITHUB_TOKEN is not configured")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.settings.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _repo_url(self, repo_name: str) -> str:
        return f"https://api.github.com/repos/{self.settings.github_owner}/{repo_name}"

    async def get_repo(self, repo_name: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._repo_url(repo_name), headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def create_repo_from_template(self, repo_name: str, private: bool = True) -> dict:
        url = (
            f"https://api.github.com/repos/{self.settings.github_owner}/"
            f"{self.settings.github_template_repo}/generate"
        )
        payload = {
            "owner": self.settings.github_owner,
            "name": repo_name,
            "private": private,
            "include_all_branches": False,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            if response.status_code == 422:
                # Repo probably already exists. Reuse it so repeated clicks are safe.
                return await self.get_repo(repo_name)
            response.raise_for_status()
            return response.json()

    async def _get_branch_ref(self, repo_name: str, branch: str = "main") -> dict:
        url = f"{self._repo_url(repo_name)}/git/ref/heads/{branch}"
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(8):
                try:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    return response.json()
                except Exception as exc:
                    last_error = exc
                    await asyncio.sleep(1)
        raise RuntimeError(f"Could not read GitHub branch ref for {repo_name}: {last_error}")

    async def upload_directory(self, repo_name: str, source_dir: Path, branch: str = "main") -> dict:
        if not source_dir.exists() or not source_dir.is_dir():
            raise FileNotFoundError(f"Generated site folder not found: {source_dir}")

        entries: list[dict] = []
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            relative_parts = path.relative_to(source_dir).parts
            if any(part in IGNORED_DIRS for part in relative_parts):
                continue
            if path.name in IGNORED_FILES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Current site template is text-only. Skip unexpected binary files.
                continue
            entries.append(
                {
                    "path": "/".join(relative_parts),
                    "mode": "100644",
                    "type": "blob",
                    "content": content,
                }
            )

        if not entries:
            raise RuntimeError(f"No uploadable files found in {source_dir}")

        async with httpx.AsyncClient(timeout=60) as client:
            ref = await self._get_branch_ref(repo_name, branch)
            current_commit_sha = ref["object"]["sha"]

            commit_response = await client.get(
                f"{self._repo_url(repo_name)}/git/commits/{current_commit_sha}",
                headers=self.headers,
            )
            commit_response.raise_for_status()
            base_tree_sha = commit_response.json()["tree"]["sha"]

            tree_response = await client.post(
                f"{self._repo_url(repo_name)}/git/trees",
                headers=self.headers,
                json={"base_tree": base_tree_sha, "tree": entries},
            )
            tree_response.raise_for_status()
            new_tree_sha = tree_response.json()["sha"]

            new_commit_response = await client.post(
                f"{self._repo_url(repo_name)}/git/commits",
                headers=self.headers,
                json={
                    "message": "Publish generated business website",
                    "tree": new_tree_sha,
                    "parents": [current_commit_sha],
                },
            )
            new_commit_response.raise_for_status()
            new_commit = new_commit_response.json()

            update_ref_response = await client.patch(
                f"{self._repo_url(repo_name)}/git/refs/heads/{branch}",
                headers=self.headers,
                json={"sha": new_commit["sha"], "force": False},
            )
            update_ref_response.raise_for_status()

        return {"commit_sha": new_commit["sha"], "files_uploaded": len(entries), "branch": branch}

    async def delete_repo(self, repo_name: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(self._repo_url(repo_name), headers=self.headers)
            response.raise_for_status()
