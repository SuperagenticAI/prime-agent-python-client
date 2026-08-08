# Demo

The demo uses a small, intentionally incomplete Python project. Copy it to a
temporary directory so Prime Agent can edit it without changing this checkout.

## Standalone Python client

From the repository root:

```bash
cp -R examples/demo_project /tmp/prime-agent-python-demo

uv run --no-project --with prime-agent-python-client examples/stream_prompt.py \
  --repository /tmp/prime-agent-python-demo \
  --provider github-copilot \
  --model gpt-4.1 \
  "Implement summarize_orders in order_summary.py and run the unit tests"
```

The script streams assistant text and prints the final Prime Agent session
statistics. Prime Agent credentials and model access must already be configured.

## SuperQode HarnessSpec

Use a fresh copy so the second run starts from the same source:

```bash
cp -R examples/demo_project /tmp/prime-agent-superqode-demo
cd /tmp/prime-agent-superqode-demo

uvx --from superqode==0.2.82 superqode harness doctor \
  --spec prime-agent.yaml \
  --json

uvx --from superqode==0.2.82 superqode harness run \
  --spec prime-agent.yaml \
  --prompt "Implement summarize_orders in order_summary.py and run the unit tests" \
  --provider github-copilot \
  --model gpt-4.1 \
  --stream

python -m unittest -v
```

The demo uses only the Python standard library. The initial unit-test failure is
intentional; the requested implementation makes it pass.
