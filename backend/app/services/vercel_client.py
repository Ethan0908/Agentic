from __future__ import annotations

import asyncio

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

    @staticmethod
    def _https_url(value: str | None) -> str | None:
        if not value:
            return None
        return value if value.startswith("http") else f"https://{value}"

    async def get_project(self, project_id_or_name: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self._with_team(f"https://api.vercel.com/v9/projects/{project_id_or_name}"),
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def create_project_for_github_repo(self, project_name: str, github_repo_full_name: str) -> dict:
        payload: dict = {
            "name": project_name,
            "framework": "nextjs",
            "gitRepository": {"type": "github", "repo": github_repo_full_name},
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self._with_team("https://api.vercel.com/v11/projects"),
                headers=self.headers,
                json=payload,
            )
            if response.status_code == 409:
                return await self.get_project(project_name)
            response.raise_for_status()
            return response.json()

    async def create_deployment_from_github(self, project_name: str, github_repo_id: int | str, ref: str = "main") -> dict:
        payload = {
            "name": project_name,
            "project": project_name,
            "target": "production",
            "gitSource": {
                "type": "github",
                "repoId": str(github_repo_id),
                "ref": ref,
            },
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self._with_team("https://api.vercel.com/v13/deployments"),
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def get_deployment(self, deployment_id_or_url: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self._with_team(f"https://api.vercel.com/v13/deployments/{deployment_id_or_url}"),
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def wait_for_deployment_ready(self, deployment: dict, timeout_seconds: int = 240, poll_seconds: int = 5) -> dict:
        deployment_id = deployment.get("id") or deployment.get("uid") or deployment.get("url")
        if not deployment_id:
            return deployment

        deadline = asyncio.get_event_loop().time() + timeout_seconds
        latest = deployment
        while asyncio.get_event_loop().time() < deadline:
            latest = await self.get_deployment(str(deployment_id))
            state = (latest.get("readyState") or latest.get("state") or "").upper()
            if state == "READY":
                return latest
            if state in {"ERROR", "CANCELED", "FAILED"}:
                raise RuntimeError(f"Vercel deployment failed with state={state}: {latest}")
            await asyncio.sleep(poll_seconds)
        return latest

    def public_url_for_project(self, project: dict, deployment: dict | None = None) -> str | None:
        deployment = deployment or {}

        for key in ("alias", "aliases"):
            aliases = deployment.get(key)
            if isinstance(aliases, list) and aliases:
                first = aliases[0]
                if isinstance(first, str):
                    return self._https_url(first)
                if isinstance(first, dict):
                    return self._https_url(first.get("domain") or first.get("url"))

        targets = project.get("targets") or {}
        production = targets.get("production") or {}
        aliases = production.get("alias") or production.get("aliases") or []
        if isinstance(aliases, list) and aliases:
            first = aliases[0]
            if isinstance(first, str):
                return self._https_url(first)
            if isinstance(first, dict):
                return self._https_url(first.get("domain") or first.get("url"))

        project_name = project.get("name")
        if project_name:
            return f"https://{project_name}.vercel.app"

        return self._https_url(deployment.get("url"))

    async def delete_project(self, project_id_or_name: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                self._with_team(f"https://api.vercel.com/v9/projects/{project_id_or_name}"),
                headers=self.headers,
            )
            response.raise_for_status()
