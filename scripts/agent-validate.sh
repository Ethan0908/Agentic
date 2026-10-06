#!/usr/bin/env bash
set -euo pipefail echo echo 
"======================================" echo " Autonomous 
validation" echo "======================================" echo 
echo "Checking Git whitespace/errors..." git diff --cached 
--check VALIDATION_RAN=0
# Python
if [[ -f pyproject.toml || -f requirements.txt || -f setup.py ]]; 
then
    echo echo "Python project detected." python3 -m compileall -q 
    . \
        -x '(\.git|\.venv|venv|node_modules)' if command -v 
    pytest >/dev/null 2>&1; then
        echo "Running pytest..." pytest -q fi if command -v ruff 
    >/dev/null 2>&1; then
        echo "Running Ruff..." ruff check . fi VALIDATION_RAN=1 
fi
# Node / JavaScript / TypeScript
if [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then 
    echo echo "Node project detected." npm test --if-present npm 
    run lint --if-present npm run typecheck --if-present npm run 
    build --if-present VALIDATION_RAN=1
fi
# Rust
if [[ -f Cargo.toml ]] && command -v cargo >/dev/null 2>&1; then 
    echo echo "Rust project detected." cargo check cargo test 
    VALIDATION_RAN=1
fi
# Go
if [[ -f go.mod ]] && command -v go >/dev/null 2>&1; then echo 
    echo "Go project detected." go test ./... VALIDATION_RAN=1
fi if [[ "$VALIDATION_RAN" -eq 0 ]]; then echo echo "WARNING:" 
    echo "No language-specific validation was detected." echo 
    "Only Git validation was performed."
fi echo
echo "Validation completed successfully."
