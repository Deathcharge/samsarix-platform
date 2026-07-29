# Example agent-project manifest

This fixture demonstrates an optional provider SDK and secret. From the repository root, run:

```console
samsarix-platform doctor examples/agent-project/samsarix-stack.toml
```

Without the optional SDK or key, the command reports warnings and exits `0`. Add `--strict` when CI should treat optional warnings as exit `1`. The CLI reports only whether `OPENAI_API_KEY` is present; it never prints the value or contacts OpenAI.
