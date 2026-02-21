# Examples

Example recipes for using the `long-running-agents` package.

## Prerequisites

- Python 3.10+
- OpenAI API key
- Package installed: `pip install long-running-agents`

Set your API key:

```bash
export OPENAI_API_KEY=sk-your-key-here
# Or create .env in the current directory with OPENAI_API_KEY=...
```

## How to run

After installing from PyPI or from source:

```bash
python -m long_running_agents.examples.01_basic_chat
python -m long_running_agents.examples.02_single_turn "Your question here"
```

## Examples

| Module | Description |
|--------|-------------|
| `01_basic_chat` | Chat loop: run multiple turns, memory persists across runs |
| `02_single_turn` | One-off query: ask a question, get a response, exit |

## Using the CLI instead

For interactive chat, you can also use the CLI:

```bash
lra chat
```

For custom agents:

```bash
lra create-agent my_agent --prompt "You are a coding assistant"
lra run my_agent
```
