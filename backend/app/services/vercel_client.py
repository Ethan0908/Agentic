from __future__ import annotations

import httpx

from app.core.config import get_settings


class VercelClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.vercel_token:
            raise RuntimeError("VERCEL_TOKEN is not configured")
        self.headers = {
            "Authorization": f"Bearer {self.settings.vercel_token}",
            "Content-Type": "application/json",
        }

    def _with_team(self, url: str) -> str:
        if self.settings.vercel_team_id:
            separator = "&" if "?" in url else "?"
            return f"{url}{separator}teamId={self.settings.vercel_team_id}"
        return url

    async def create_project_for_github_repo(self, project_name: str, github_repo_id: int | None = None) -> dict:
        payload: dict = {"name": project_name, "framework": "nextjs"}
        if github_repo_id:
            payload["gitRepository"] = {"type": "github", "repoId": github_repo_id}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self._with_team("https://api.vercel.com/v11/projects"),
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def delete_project(self, project_id_or_name: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                self._with_team(f"https://api.vercel.com/v9/projects/{project_id_or_name}"),
                headers=self.headers,
            )
            response.raise_for_status()
