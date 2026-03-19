# Goal Agent — Intelligent Planning System

An AI-powered planning agent that takes a high-level goal, asks smart clarifying questions when needed, and generates a **complete, structured roadmap** — not a step-by-step task runner.

## How It Works

```
Goal Input → Clarification (if needed) → Complete Structured Plan
```

1. **You enter a goal** — e.g., "Learn machine learning" or "Build a SaaS startup"
2. **The agent asks clarifying questions** if the goal is vague (timeline, experience, constraints)
3. **A full plan is generated** with timeline, phases, tasks, resources, and strategy

> This is a **strategic advisor**, not a task runner. It does NOT execute tasks or mark them as done.

## Running

```bash
pip install -r requirements.txt
python app.py
```

Open **http://localhost:1644**

### Azure OpenAI (optional)

Create a `.env` file:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

The app works without API keys using a built-in simulation engine.

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/start` | Submit a goal → clarification questions or full plan |
| `POST` | `/clarify` | Submit answers → full structured plan |
| `POST` | `/reset` | Clear state |

## Project Structure

```
Goal Agent Study/
├── app.py                     # Flask server (port 1644)
├── agent/
│   ├── state.py               # PlannerState (goal + answers + plan)
│   ├── llm.py                 # Azure OpenAI + simulation fallback
│   └── planner.py             # Clarification + plan generation
├── templates/
│   └── index.html             # Single-page UI
├── static/
│   ├── css/style.css          # Dark glassmorphism theme
│   └── js/app.js              # Frontend logic
├── requirements.txt
└── README.md
```
