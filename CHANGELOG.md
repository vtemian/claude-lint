# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2025-11-24

### Critical Fixes
- Fixed IndexError when resuming progress with changed batch count
  - Validates loaded progress matches current batch count
  - Discards stale progress and starts fresh on mismatch
  - Prevents crashes when files are added/removed between runs

### Major Features
- **Streaming output**: Results written incrementally to file as batches complete
  - Text format: File updates in real-time as analysis progresses
  - JSON format: JSON Lines (NDJSON) - one object per line
  - Can review violations while analysis is still running
  - Partial results preserved if process is interrupted
  - Use: `--output report.txt` or `--json -o report.jsonl`

- **Detailed progress feedback**: Shows current processing step during analysis
  - "Reading files" - Loading file contents
  - "Building prompt" - Constructing API request
  - "Calling Claude API" - During API call (longest wait)
  - "Processing response" - Parsing results
  - "Updating cache" - Saving to cache
  - Provides continuous feedback during long-running analyses

- **File output option**: Save analysis results to file
  - Use `--output <file>` or `-o <file>` flag
  - Results written to file and displayed to stdout
  - Perfect for CI/CD pipelines and archiving reports

### Testing
- Added comprehensive tests for all new features
- All 164 tests passing
- Test coverage maintained at 90%+

## [0.2.0] - 2025-11-11

### Critical Fixes
- Added 30-second timeout to all git subprocess calls to prevent hanging
- Replaced print() statements with proper logging framework
- Implemented atomic file writes for cache and progress files
- Fixed exception handling to not catch KeyboardInterrupt/SystemExit
- Removed unused gitpython dependency

### Major Improvements
- Unified pattern matching to use PurePath.match() consistently
- Made Claude model configurable via config file
- Improved file encoding handling with UTF-8 and latin-1 fallback
- Added comprehensive input validation for all parameters
- Implemented Anthropic client reuse for better performance
- Added --verbose, --quiet, and --version CLI flags
- Added file size limits (configurable, default 1MB)

### Minor Improvements
- Added TypedDict for violation structures
- Added __all__ exports for public API
- Normalized config keys to snake_case (with camelCase backwards compat)
- Comprehensive documentation (architecture, troubleshooting)
- Improved error messages to stderr
- Better type safety throughout
- Fixed type checking issues (mypy) and linting (ruff)

### Documentation
- Added ARCHITECTURE.md with design decisions
- Added TROUBLESHOOTING.md for common issues
- Updated README with all new features
- Added inline documentation improvements

## [0.1.0] - 2025-11-11

Initial release with core functionality:
- Smart caching based on file and CLAUDE.md hashes
- Multiple scan modes: full project, git diff, working directory, staged files
- Batch processing for large projects
- Progress tracking with resume capability
- Prompt caching for cost efficiency
