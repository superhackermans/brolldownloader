"""
Wrapper that calls Claude via the `claude` CLI (Claude Code Max mode).
No API key needed -- runs for free under Max subscription.
"""
import subprocess
import tempfile
import os


def call_claude(prompt: str, model: str = "sonnet", max_tokens: int = None) -> str:
    """Call Claude via Claude Code CLI subprocess."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        # Map model names to claude CLI model IDs
        model_map = {
            "sonnet": "claude-sonnet-4-6",
            "opus": "claude-opus-4-6",
            "haiku": "claude-haiku-4-5-20251001",
        }
        model_id = model_map.get(model, model)

        cmd = [
            "claude",
            "-p",
            "--output-format", "text",
            "--model", model_id,
            "--dangerously-skip-permissions",
        ]

        with open(prompt_file, 'r') as pf:
            result = subprocess.run(
                cmd,
                stdin=pf,
                capture_output=True,
                text=True,
                timeout=600
            )

        if result.returncode != 0:
            stderr = result.stderr or ""
            # If there's still stdout, use it (some errors are warnings)
            if result.stdout and result.stdout.strip():
                return result.stdout.strip()
            raise RuntimeError(f"Claude CLI error (exit {result.returncode}): {stderr[:500]}")

        return result.stdout.strip()

    finally:
        os.unlink(prompt_file)


def call_claude_with_file(prompt: str, file_path: str) -> str:
    """Call Claude with file contents inlined."""
    full_prompt = f"{prompt}\n\nFile contents of {file_path}:\n<file>\n{open(file_path).read()}\n</file>"
    return call_claude(full_prompt)
