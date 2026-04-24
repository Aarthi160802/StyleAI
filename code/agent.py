"""
agent.py – Agentic loop for StyleAI.

Flow:
  Query → Gemini → (TOOL_CALL detected?) → Execute tool → append result →
  Query → Gemini → ... → FINAL RECOMMENDATION

All steps are yielded as structured dicts so the Streamlit UI can render them
progressively without blocking.
"""

import json
import re
import time
import textwrap
from typing import Generator

import google.generativeai as genai

from code.config import GEMINI_API_KEY, GEMINI_MODEL, MAX_AGENT_STEPS
from code.tools import TOOL_REGISTRY
from prompts.stylist_prompt import SYSTEM_PROMPT, TOOL_RESULT_TEMPLATE

# ── Configure Gemini ──────────────────────────────────────────────────────────

def _configure_gemini():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Please add it to your .env file.")
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL)


# ── Tool description builder ──────────────────────────────────────────────────

def _build_tool_descriptions() -> str:
    lines = []
    for name, meta in TOOL_REGISTRY.items():
        lines.append(f"  {meta['emoji']} {name}({', '.join(meta['params'])})")
        lines.append(f"     → {meta['description']}")
    return "\n".join(lines)


# ── Tool call parser ──────────────────────────────────────────────────────────
_TOOL_CALL_RE = re.compile(
    r"TOOL_CALL:\s*(?P<name>\w+)\s*\|(?P<args>[^$\n]+)", re.IGNORECASE
)


def _parse_tool_call(text: str):
    """Return (tool_name, kwargs_dict) or None if no tool call found."""
    match = _TOOL_CALL_RE.search(text)
    if not match:
        return None
    tool_name = match.group("name").strip()
    raw_args  = match.group("args").strip()
    kwargs = {}
    for part in raw_args.split("|"):
        if "=" in part:
            k, _, v = part.partition("=")
            kwargs[k.strip()] = v.strip()
    return tool_name, kwargs


def _invoke_tool(tool_name: str, kwargs: dict) -> str:
    """Call the tool function and return a JSON string of the result."""
    if tool_name not in TOOL_REGISTRY:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    fn = TOOL_REGISTRY[tool_name]["fn"]
    # Cast numeric kwargs
    sig_params = TOOL_REGISTRY[tool_name]["params"]
    for p in sig_params:
        name_part = p.split("(")[0].strip().split()[0]
        if "int" in p and name_part in kwargs:
            try:
                kwargs[name_part] = int(kwargs[name_part])
            except ValueError:
                pass
    try:
        result = fn(**kwargs)
    except TypeError as exc:
        result = {"error": f"Tool call error: {exc}"}
    return json.dumps(result, indent=2, ensure_ascii=False)


# ── Agent step type definitions ───────────────────────────────────────────────
# Each yielded dict has:
#   type: "thinking" | "tool_call" | "tool_result" | "final" | "error"
#   content: str
#   tool_name (optional): str
#   tool_args (optional): dict

# ── Main agentic loop ─────────────────────────────────────────────────────────

def run_agent(user_query: str) -> Generator[dict, None, None]:
    """
    Generator that runs the full agentic loop.
    Yields step dicts for the UI to render progressively.
    """
    try:
        model = _configure_gemini()
    except ValueError as exc:
        yield {"type": "error", "content": str(exc)}
        return

    system_prompt = SYSTEM_PROMPT.format(
        tool_descriptions=_build_tool_descriptions()
    )

    # Build conversation history as a list of {"role": ..., "parts": [...]}
    history = []

    # ── Step 0: initial query ─────────────────────────────────────────────────
    history.append({"role": "user", "parts": [system_prompt + "\n\n" + user_query]})

    steps_taken = 0
    final_reached = False

    while steps_taken < MAX_AGENT_STEPS and not final_reached:
        steps_taken += 1

        # ── Call Gemini (with retry on 429 rate-limit) ────────────────────
        _MAX_RETRIES = 3
        llm_text = None
        for attempt in range(_MAX_RETRIES):
            try:
                chat     = model.start_chat(history=history[:-1])
                resp     = chat.send_message(history[-1]["parts"][0])
                llm_text = resp.text
                break  # success
            except Exception as exc:
                err_str = str(exc)
                # Parse retry_delay from the 429 message if present
                if "429" in err_str or "quota" in err_str.lower():
                    # Try to extract seconds from message, default to 60s
                    import re as _re
                    m = _re.search(r"retry.*?(\d+)\s*s", err_str, _re.IGNORECASE)
                    wait = int(m.group(1)) + 5 if m else 60
                    wait = min(wait, 90)  # cap at 90s
                    if attempt < _MAX_RETRIES - 1:
                        yield {
                            "type":    "thinking",
                            "content": f"⏳ Rate limit hit (429). Waiting {wait}s before retry {attempt+2}/{_MAX_RETRIES}…",
                            "step":    steps_taken,
                        }
                        time.sleep(wait)
                        continue
                yield {"type": "error", "content": f"Gemini API error: {exc}"}
                return

        if llm_text is None:
            yield {"type": "error", "content": "Gemini did not respond after retries. Please wait a minute and try again."}
            return

        # ── Yield thinking step ───────────────────────────────────────────────
        yield {"type": "thinking", "content": llm_text, "step": steps_taken}

        # ── Check for tool call ───────────────────────────────────────────────
        parsed = _parse_tool_call(llm_text)

        if parsed:
            tool_name, tool_kwargs = parsed
            yield {
                "type":      "tool_call",
                "content":   f"Calling **{tool_name}** with args: `{tool_kwargs}`",
                "tool_name": tool_name,
                "tool_args": tool_kwargs,
                "step":      steps_taken,
            }

            # Execute tool
            tool_result_str = _invoke_tool(tool_name, tool_kwargs)
            yield {
                "type":      "tool_result",
                "content":   tool_result_str,
                "tool_name": tool_name,
                "step":      steps_taken,
            }

            # Append assistant message and tool result to history
            history.append({"role": "model", "parts": [llm_text]})
            follow_up = TOOL_RESULT_TEMPLATE.format(
                tool_name=tool_name,
                tool_result=tool_result_str,
            )
            history.append({"role": "user", "parts": [follow_up]})

        else:
            # No tool call → treat as final answer
            history.append({"role": "model", "parts": [llm_text]})
            final_reached = True
            yield {"type": "final", "content": llm_text, "step": steps_taken}

    if not final_reached:
        yield {
            "type":    "error",
            "content": f"Agent reached maximum steps ({MAX_AGENT_STEPS}) without a final answer.",
        }
