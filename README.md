# Goal Agent: Professional LangGraph Planning System

An advanced, multi-node AI agent designed for **Strategic Planning** — not just task lists. This agent uses **LangGraph** to autonomously research, critique, and optimize high-level roadmaps for goals ranging from 8 weeks to 5 years.

---

## 🚀 Key Features

- **🧠 Multi-Node Agentic Brain**: Uses LangGraph to route between clarification, planning, and refinement.
- **🌐 Real-Time Internet Search**: An autonomous **SearchNode** using DuckDuckGo to find real-world conferences, webinars, and events in 2026.
- **🔄 Self-Improving Logic**: A built-in **Critic/Optimizer** loop that self-scores and improves plans (1-10) before showing them to you.
- **📅 Flexible Temporal Scaling**: Dynamically switches between **Weeks, Months, or Years** based on your goal's duration.
- **🎨 Modern SaaS Interface**: 2-column dashboard (Notion/Linear style) with interactive accordions, horizontal steppers, and inline event suggestions.
- **🗓️ Calendar Export**: One-click download of `.ics` files for your entire roadmap or individual events.
- **✏️ Interactive Refinement**: Refine your plan by simply chatting with the AI after generation.

---

## 🚦 Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Open the Dashboard**:
   Visit **[http://localhost:1644](http://localhost:1644)**

---

## 🛠️ Configuration

The system is optimized for **Azure OpenAI (gpt-4o)**. Create a `.env` file in the root directory:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

---

## 📁 Project Structure

```text
Goal Agent Study/
├── app.py                     # Flask Server (Endpoints: /start, /clarify, /refine)
├── agent/
│   ├── graph.py               # 🔗 LangGraph Orchestration (8 Nodes)
│   ├── state.py               # Shared AgentState TypedDict
│   ├── llm.py                 # Azure OpenAI + fallback logic
│   └── nodes/                 # 🧩 Modular Agent Nodes
│       ├── router.py          # Intent analysis
│       ├── clarifier.py       # Pill-based follow-up questions
│       ├── planner.py         # Core roadmap generation
│       ├── search.py          # Internet search & event discovery
│       ├── critic.py          # Self-assessment node
│       ├── optimizer.py       # Iterative improvement node
│       ├── formatter.py       # JSON normalization
│       └── refinement.py      # Conversation-based plan editing
├── static/
│   ├── css/style.css          # Sleek Light Theme (SaaS Dashboard)
│   └── js/app.js              # State-driven Frontend (State → UI)
└── templates/
    └── index.html             # Single-page modern dashboard
```

---

## 📘 Documentation

For a deep dive into the technical workings, internal loops, and node logic, see:
- **[SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)** — Comprehensive architecture guide.
