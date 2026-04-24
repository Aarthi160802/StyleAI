# 👗 StyleAI — Agentic AI Fashion Stylist

> **EAG V3 · Assignment 3** — Agentic AI with Multi-Step Tool Calling

---

## 🎬 Demo Video

[![StyleAI Demo](https://img.shields.io/badge/▶%20Watch%20Demo-YouTube-red?style=for-the-badge&logo=youtube)](https://youtu.be/hfJRaqNxnJQ)

---

## 🧠 What is StyleAI?

StyleAI is a fully **Agentic AI** personal fashion stylist built with **Google Gemini** and **Streamlit**. It doesn't just answer a question — it **reasons**, **calls external tools**, **synthesises real-world data**, and delivers a personalised outfit recommendation.

Given your event, body, and style preferences, the agent:

1. Checks **live weather** at your event location
2. Fetches **latest fashion news & trend headlines**
3. Retrieves **seasonal colour palette** for your skin tone
4. Looks up **dress code rules** for your event type
5. Pulls **outfit inspiration images** (Pexels) for a visual moodboard
6. Synthesises everything into a **final styled recommendation**

---

## 🤖 Agentic Loop — How It Works

This is the core of the assignment. StyleAI calls Gemini **multiple times in a loop**, where every LLM response can trigger a tool call, whose result is fed back into the next prompt — until the agent reaches a final answer.

```
User Query
    │
    ▼
┌─────────────────────────────────────────────┐
│  LLM Call (Gemini)                          │
│  → Reasons about what data it needs         │
│  → Outputs: TOOL_CALL: get_weather | ...    │
└────────────────┬────────────────────────────┘
                 │ Tool detected
                 ▼
        🛠️ Tool Executed
        (real API call)
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  Tool Result appended to conversation       │
│  → New prompt: "Tool returned X. Continue" │
└────────────────┬────────────────────────────┘
                 │
                 ▼
        🔁 Repeat (up to 8 steps)
                 │
                 ▼
        ✅ FINAL RECOMMENDATION
```

**Every single step is displayed live in the UI** — users see the agent's thinking, each tool call with its arguments, and the raw tool result, before the final answer appears.

---

## 🛠️ 5 Custom Tool Functions

| # | Tool | API | What it does |
|---|------|-----|-------------|
| 1 | `get_weather` | OpenWeatherMap | Fetches live temperature, humidity, wind, description + fabric advice for the event city & date |
| 2 | `get_fashion_news` | NewsAPI | Retrieves the latest fashion & trend headlines matching a query |
| 3 | `get_outfit_images` | Pexels | Searches for outfit inspiration photos; feeds the visual moodboard |
| 4 | `get_color_palette` | Internal | Derives a seasonal colour palette (Spring/Summer/Autumn/Winter) + skin-tone tips |
| 5 | `get_dress_code_guide` | Internal | Returns detailed dress-code rules, do's & don'ts for 8 event types |

---

## 🌐 External APIs Used

### 1. Google Gemini (`gemini-2.5-flash`)
- **Provider:** Google AI Studio
- **Used for:** The core LLM — called multiple times in the agentic loop to reason, decide which tool to call next, and produce the final outfit recommendation
- **Free tier:** 15 RPM on `gemini-2.0-flash`, 5 RPM on `gemini-2.5-flash`
- **Docs:** [aistudio.google.com](https://aistudio.google.com/app/apikey)

### 2. OpenWeatherMap
- **Used for:** `get_weather` tool — live temperature, humidity, wind speed, and weather description for any city
- **Endpoint:** `GET /weather` (current weather, free tier)
- **Free tier:** 60 calls/minute, no credit card required
- **Docs:** [openweathermap.org/api](https://openweathermap.org/api)

### 3. NewsAPI
- **Used for:** `get_fashion_news` tool — fetches latest news articles matching a fashion/trend keyword query
- **Endpoint:** `GET /v2/everything`
- **Free tier:** 100 requests/day (developer plan)
- **Docs:** [newsapi.org](https://newsapi.org)

### 4. Pexels
- **Used for:** `get_outfit_images` tool — searches for high-quality outfit photos to populate the Pinterest-style moodboard
- **Endpoint:** `GET /v1/search` with `Authorization: <key>` header
- **Free tier:** 200 requests/hour, no credit card required
- **Docs:** [pexels.com/api](https://www.pexels.com/api/)

---

## 📋 LLM Conversation Log Format

Each agent run is saved as a timestamped JSON in `logs/`. Here's the structure:

```json
{
  "timestamp": "2026-04-24T18:30:00",
  "form_data": { "event_type": "Wedding", "event_city": "Mumbai", ... },
  "agent_steps": [
    { "step": 1, "type": "thinking",    "content_preview": "I need weather data..." },
    { "step": 1, "type": "tool_call",   "tool_name": "get_weather", "tool_args": {...} },
    { "step": 1, "type": "tool_result", "tool_name": "get_weather", "content_preview": "{...}" },
    { "step": 2, "type": "thinking",    "content_preview": "Weather is 32°C. Now fashion news..." },
    ...
    { "step": 5, "type": "final",       "content_preview": "### FINAL OUTFIT RECOMMENDATION..." }
  ],
  "final_answer": "### FINAL OUTFIT RECOMMENDATION\n..."
}
```

> 📄 Full session logs (including all LLM responses) are viewable in the **📋 Session Logs** tab.

---

## 📁 Project Structure

- **`app.py`** — Streamlit UI entry point; defines all 4 tabs, custom CSS theming, and the sidebar
- **`requirements.txt`** — Python package dependencies
- **`.env`** — API keys (not committed to version control)

- **`code/`** — Core application package
  - **`agent.py`** — Agentic loop: calls Gemini multiple times, detects tool calls, feeds results back, retries on rate limits
  - **`tools.py`** — 5 custom tool functions plus the Pexels moodboard image helper
  - **`config.py`** — Centralised API key loader via `python-dotenv`
  - **`logger.py`** — Saves and reads JSON session logs

- **`prompts/`** — All LLM prompt templates
  - **`stylist_prompt.py`** — System prompt, user query template, and tool result template

- **`logs/`** — Auto-saved JSON session logs, one file per agent run (e.g. `session_20260424_183000.json`)

---

## 🖥️ UI — 4 Tabs

| Tab | Purpose |
|-----|---------|
| **👗 Inputs** | Three sections: Event Details · Personal Details · Style Preferences |
| **✨ Outfit Recommendation** | Live agentic reasoning chain → final recommendation → auto-generated moodboard |
| **📌 Style Inspiration** | Pinterest-style masonry board · Pexels search · Seasonal colour palette |
| **📋 Session Logs** | Browse, inspect and replay all past agent runs as JSON |

---

## ⚙️ API Keys Required

| Key | Required | Free Tier | Get It |
|-----|----------|-----------|--------|
| `GEMINI_API_KEY` | ✅ | Yes | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `OPENWEATHER_API_KEY` | ✅ | Yes | [openweathermap.org/api](https://openweathermap.org/api) |
| `NEWS_API_KEY` | ✅ | Yes | [newsapi.org/register](https://newsapi.org/register) |
| `PEXELS_API_KEY` | ✅ | Yes | [pexels.com/api](https://www.pexels.com/api/) |

---

## 🚀 Setup & Run

```bash
# 1. Clone / navigate to the project
cd "Assignment-3-StyleAI"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
copy .env.example .env
# → Open .env and fill in your API keys

# 4. Run
streamlit run app.py
```

---

## 🔑 Assignment Checklist

| Requirement | Status |
|-------------|--------|
| LLM called multiple times in a loop | ✅ Up to 8 steps |
| Full conversation history passed each call | ✅ `history[]` accumulates all turns |
| At least 3 custom tool functions | ✅ 5 tools |
| Agent reasoning chain displayed in UI | ✅ Thinking / Tool Call / Tool Result per step |
| External API usage | ✅ OpenWeatherMap · NewsAPI · Pexels |
| Final answer clearly shown | ✅ `### FINAL OUTFIT RECOMMENDATION` |
| Session logs saved | ✅ JSON in `logs/` |
| Rate-limit retry logic | ✅ Auto-retry with parsed wait time |

---

## 📝 Sample LLM Log (copy-paste for submission)

> After running the agent, go to **📋 Session Logs** tab → select the session → expand **Raw JSON Log** → copy and paste the full JSON for your submission.

---

*Built with ❤️ using Google Gemini · Streamlit · OpenWeatherMap · NewsAPI · Pexels*
