# claude-lint

CLAUDE.md compliance checker using Claude API with prompt caching.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Check changed files from main branch
claude-lint --diff main

# Check working directory changes
claude-lint --working

# Full project scan
claude-lint --full
```

## Configuration

Create `.agent-lint.json`:

```json
{
  "include": ["**/*.py", "**/*.js", "**/*.ts"],
  "exclude": ["node_modules/**", "dist/**", "*.test.js"],
  "batchSize": 10
}
```
