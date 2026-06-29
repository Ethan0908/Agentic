from __future__ import annotations

import httpx

from app.core.config import get_settings


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
            response.raise_for_status()
            return response.json()

    async def delete_repo(self, repo_name: str) -> None:
        url = f"https://api.github.com/repos/{self.settings.github_owner}/{repo_name}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(url, headers=self.headers)
            response.raise_for_status()
