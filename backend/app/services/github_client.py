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

    def _split_repo(self, repo_name_or_full_name: str) -> tuple[str, str]:
        if "/" in repo_name_or_full_name:
            owner, repo = repo_name_or_full_name.split("/", 1)
            return owner, repo
        return self.settings.github_owner, repo_name_or_full_name

    def _repo_url(self, repo_name_or_full_name: str) -> str:
        owner, repo = self._split_repo(repo_name_or_full_name)
        return f"https://api.github.com/repos/{owner}/{repo}"

    async def get_repo(self, repo_name_or_full_name: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._repo_url(repo_name_or_full_name), headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def create_repo(self, repo_name: str, private: bool = True) -> dict:
        """Create or reuse a generated repo.

        GitHub's /user/repos endpoint creates the repo under the authenticated
        account. We store the returned full_name later, so later steps do not
        have to guess the owner again.
        """
        try:
            return await self.get_repo(repo_name)
        except Exception:
            pass

        payload = {
            "name": repo_name,
            "private": private,
            "auto_init": True,
            "description": "Generated business website preview.",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.github.com/user/repos", headers=self.headers, json=payload)
            if response.status_code == 422:
                # Repo probably exists. Try the configured owner one more time,
                # then return the precise API error if that lookup still fails.
                return await self.get_repo(repo_name)
            response.raise_for_status()
            return response.json()

    async def create_repo_from_template(self, repo_name: str, private: bool = True) -> dict:
        if not self.settings.github_template_repo:
            return await self.create_repo(repo_name, private=private)

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
                return await self.get_repo(repo_name)
            response.raise_for_status()
            return response.json()

    async def _get_branch_ref(self, repo_name_or_full_name: str, branch: str = "main") -> dict:
        url = f"{self._repo_url(repo_name_or_full_name)}/git/ref/heads/{branch}"
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(15):
                try:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    return response.json()
                except Exception as exc:
                    last_error = exc
                    await asyncio.sleep(1)
        raise RuntimeError(f"Could not read GitHub branch ref for {repo_name_or_full_name}: {last_error}")

    def _directory_entries(self, source_dir: Path, target_prefix: str | None = None) -> list[dict]:
        if not source_dir.exists() or not source_dir.is_dir():
            raise FileNotFoundError(f"Generated site folder not found: {source_dir}")

        clean_prefix = (target_prefix or "").strip("/")
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
                continue

            relative_path = "/".join(relative_parts)
            target_path = f"{clean_prefix}/{relative_path}" if clean_prefix else relative_path
            entries.append(
                {
                    "path": target_path,
                    "mode": "100644",
                    "type": "blob",
                    "content": content,
                }
            )

        if not entries:
            raise RuntimeError(f"No uploadable files found in {source_dir}")
        return entries

    async def _commit_entries(self, repo_name_or_full_name: str, entries: list[dict], branch: str, message: str) -> dict:
        async with httpx.AsyncClient(timeout=90) as client:
            ref = await self._get_branch_ref(repo_name_or_full_name, branch)
            current_commit_sha = ref["object"]["sha"]

            commit_response = await client.get(
                f"{self._repo_url(repo_name_or_full_name)}/git/commits/{current_commit_sha}",
                headers=self.headers,
            )
            commit_response.raise_for_status()
            base_tree_sha = commit_response.json()["tree"]["sha"]

            tree_response = await client.post(
                f"{self._repo_url(repo_name_or_full_name)}/git/trees",
                headers=self.headers,
                json={"base_tree": base_tree_sha, "tree": entries},
            )
            tree_response.raise_for_status()
            new_tree_sha = tree_response.json()["sha"]

            new_commit_response = await client.post(
                f"{self._repo_url(repo_name_or_full_name)}/git/commits",
                headers=self.headers,
                json={
                    "message": message,
                    "tree": new_tree_sha,
                    "parents": [current_commit_sha],
                },
            )
            new_commit_response.raise_for_status()
            new_commit = new_commit_response.json()

            update_ref_response = await client.patch(
                f"{self._repo_url(repo_name_or_full_name)}/git/refs/heads/{branch}",
                headers=self.headers,
                json={"sha": new_commit["sha"], "force": False},
            )
            update_ref_response.raise_for_status()

        return {"commit_sha": new_commit["sha"], "files_uploaded": len(entries), "branch": branch}

    async def upload_directory(self, repo_name_or_full_name: str, source_dir: Path, branch: str = "main") -> dict:
        entries = self._directory_entries(source_dir)
        return await self._commit_entries(repo_name_or_full_name, entries, branch, "Publish generated business website")

    async def upload_directory_to_path(self, repo_name_or_full_name: str, source_dir: Path, target_prefix: str, branch: str = "main") -> dict:
        entries = self._directory_entries(source_dir, target_prefix=target_prefix)
        return await self._commit_entries(repo_name_or_full_name, entries, branch, f"Archive generated website at {target_prefix}")

    async def delete_repo(self, repo_name_or_full_name: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(self._repo_url(repo_name_or_full_name), headers=self.headers)
            response.raise_for_status()
