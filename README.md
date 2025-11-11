# claude-lint

CLAUDE.md compliance checker using Claude API with prompt caching.

## Features

- 🔍 Smart change detection with git integration
- 💾 Persistent caching for fast re-runs
- 🔄 Resume capability for interrupted scans
- 📦 Batch processing with configurable size
- 🚀 Prompt caching for efficient API usage
- 🔁 Automatic retry with exponential backoff
- 📊 Detailed and JSON output formats
- ✅ CI/CD friendly with exit codes

## Installation

```bash
# From source
git clone https://github.com/yourusername/claude-lint.git
cd claude-lint
pip install -e .

# Or with pip (once published)
pip install claude-lint
```

## Configuration

Create `.agent-lint.json` in your project root:

```json
{
  "include": ["**/*.py", "**/*.js", "**/*.ts"],
  "exclude": ["node_modules/**", "dist/**", "*.test.js"],
  "batchSize": 10
}
```

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Or specify in config:

```json
{
  "apiKey": "your-api-key",
  ...
}
```

## Usage

### Full Project Scan

```bash
claude-lint --full
```

### Check Changes from Branch

```bash
claude-lint --diff main
claude-lint --diff origin/develop
```

### Check Working Directory

```bash
# Check modified and untracked files
claude-lint --working
```

### Check Staged Files

```bash
# Check only staged files
claude-lint --staged
```

### JSON Output

```bash
claude-lint --full --json > results.json
```

## CI/CD Integration

Claude-lint returns exit code 0 for clean scans and 1 when violations are found:

```yaml
# GitHub Actions example
- name: Check CLAUDE.md compliance
  run: |
    pip install claude-lint
    claude-lint --diff origin/main
```

## How It Works

1. **File Collection**: Gathers files based on mode (full/diff/working/staged) and include/exclude patterns
2. **Cache Check**: Skips files that haven't changed since last scan
3. **Batch Processing**: Groups files into batches (default 10-15)
4. **API Analysis**: Sends batches to Claude API with cached CLAUDE.md in system prompt
5. **Result Parsing**: Extracts violations from Claude's analysis
6. **Caching**: Stores results and file hashes for future runs
7. **Reporting**: Outputs detailed or JSON format with exit code

## Caching Strategy

- **CLAUDE.md Hash**: Triggers full re-scan when guidelines change
- **File Hashes**: Only re-checks modified files
- **API Prompt Caching**: Claude's prompt caching keeps CLAUDE.md cached across requests
- **Result Cache**: Stores previous analysis results in `.agent-lint-cache.json`

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=claude_lint --cov-report=html

# Lint code
ruff check src/

# Format code
ruff format src/
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
