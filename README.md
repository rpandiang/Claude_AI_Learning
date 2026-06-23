# Claude Learning

A personal workspace for exploring and learning Claude AI — covering the Claude API, Claude Code CLI, and building AI-powered applications with Anthropic's SDK.

## Goals

- Learn the Claude API and Anthropic SDK
- Experiment with prompt engineering techniques
- Build small projects and tools using Claude models
- Explore Claude Code features (hooks, MCP servers, slash commands, agents)

## Structure

```
Claude_Learning/
├── README.md
├── experiments/       # One-off scripts and prompt experiments
├── projects/          # Larger, more complete mini-projects
└── notes/             # Personal notes and learnings
```

## Getting Started

### Prerequisites

- Python 3.10+ or Node.js 18+
- An Anthropic API key ([get one here](https://console.anthropic.com/))
- Claude Code CLI (optional): `npm install -g @anthropic-ai/claude-code`

### Setup

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Install the Anthropic Python SDK
pip install anthropic

# Or the Node.js SDK
npm install @anthropic-ai/sdk
```

### Quick Example (Python)

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)

print(message.content[0].text)
```

## Key Resources

- [Anthropic Documentation](https://docs.anthropic.com/)
- [Claude API Reference](https://docs.anthropic.com/en/api/)
- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/)
- [Anthropic Cookbook (examples)](https://github.com/anthropics/anthropic-cookbook)

## Current Models

| Model | ID | Best For |
|---|---|---|
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | Balanced performance & speed |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Fast, lightweight tasks |
| Claude Opus 4.8 | `claude-opus-4-8` | Complex reasoning |
| Claude Fable 5 | `claude-fable-5` | Latest & most capable |
