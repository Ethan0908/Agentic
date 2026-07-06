from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping

PLACEHOLDER_MARKER = "AGENTIC_REPLACE_ME"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def reset_dir(path: Path, overwrite: bool = True) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(str(path))
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_minimal_project(target: Path, business: Mapping[str, Any]) -> None:
    slug = str(business.get("slug") or "generated-site")
    name = str(business.get("name") or "Generated Site")
    description = str(business.get("description") or business.get("businessType") or "Generated business website")

    write_json(target / "package.json", {
        "name": slug,
        "version": "1.0.0",
        "private": True,
        "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
        "dependencies": {"next": "^15.3.0", "react": "^19.0.0", "react-dom": "^19.0.0"},
        "devDependencies": {"@types/node": "^22.15.0", "@types/react": "^19.0.0", "@types/react-dom": "^19.0.0", "typescript": "^5.8.0"},
    })
    write_json(target / "tsconfig.json", {
        "compilerOptions": {
            "target": "es5",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": False,
            "skipLibCheck": True,
            "strict": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "plugins": [{"name": "next"}],
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
        "exclude": ["node_modules"],
    })
    write_text(target / "next.config.ts", "import type { NextConfig } from 'next';\n\nconst nextConfig: NextConfig = {};\n\nexport default nextConfig;\n")
    write_text(target / "next-env.d.ts", "/// <reference types=\"next\" />\n/// <reference types=\"next/image-types/global\" />\n")
    write_text(target / "app" / "layout.tsx", f"import type {{ Metadata }} from 'next';\nimport type {{ ReactNode }} from 'react';\nimport './globals.css';\n\nexport const metadata: Metadata = {{ title: {name!r}, description: {description!r} }};\n\nexport default function RootLayout({{ children }}: {{ children: ReactNode }}) {{\n  return <html lang=\"en\"><body>{{children}}</body></html>;\n}}\n")
    write_text(target / "app" / "page.tsx", f"import business from '../data/business.json';\n\nexport default function Home() {{\n  return <main className=\"generation-placeholder\" data-generation-marker=\"{PLACEHOLDER_MARKER}\"><p>{{business.name}}</p><h1>{PLACEHOLDER_MARKER}</h1></main>;\n}}\n")
    write_text(target / "app" / "globals.css", f":root {{ background: #0f1115; color: #f6f3ed; font-family: Arial, Helvetica, sans-serif; }}\n* {{ box-sizing: border-box; }}\nbody {{ margin: 0; min-height: 100vh; }}\n.generation-placeholder {{ min-height: 100vh; display: grid; place-items: center; padding: 48px; text-align: center; }}\n/* {PLACEHOLDER_MARKER} */\n")
    write_json(target / "data" / "business.json", business)
    write_json(target / "data" / "generation-mode.json", {"mode": "blank-scaffold", "scaffoldIsFinal": False, "placeholderMarker": PLACEHOLDER_MARKER})
    write_text(target / "GENERATION_BRIEF.md", f"# Generation brief\n\nThis folder is a blank scaffold. Remove `{PLACEHOLDER_MARKER}` and build from `data/business.json`.\n")


def assert_replaced(target: Path) -> None:
    paths = [target / "app" / "page.tsx", target / "app" / "globals.css"]
    remaining = [str(path.relative_to(target)) for path in paths if path.exists() and PLACEHOLDER_MARKER in path.read_text(encoding="utf-8")]
    if remaining:
        raise RuntimeError("Placeholder remains in: " + ", ".join(remaining))
