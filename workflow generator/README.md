# LangGraph Studio Canvas & Workflow Generator

An advanced, interactive visual workflow and flowchart generator built with **modern LangGraph 0.2+ concepts**, **multimodal vision diagram recognition**, and a precision editorial engineering interface inspired by [musthaque.netlify.app](https://musthaque.netlify.app).

---

## ✨ Key Features

1. **Dual Theme Mode (Dark & Light)**:
   - Full dark and light theme toggle in the navigation bar.
   - **Dark Mode**: Obsidian canvas with glowing circuit traces, glassmorphism cards, and high-contrast typography.
   - **Light Mode**: Clean executive slate and parchment palette (`#f8fafc`), crisp white cards with soft elevation shadows, and dark ink typography.

2. **Precision Dotted Canvas**:
   - Engineered 24px dot-matrix grid with reactive ambient lighting.

3. **Collision-Free Circuit Bezier Routing**:
   - Mathematical edge routing that arches backward/return loops **OVER** or **UNDER** intermediate nodes to prevent line crossing and card clipping.
   - Every edge label is backed with a rounded pill capsule (`<rect rx="10">`) ensuring zero text overlap.

4. **Vision & Diagram Image Recognition**:
   - **3 Ways to Upload**: File picker, drag-and-drop overlay, or direct clipboard screenshot paste (`Ctrl + V`).
   - Translates whiteboard diagrams, hand sketches, and flowchart screenshots directly into structured LangGraph systems.
   - **Dual Engine**: Client-side **Tesseract.js OCR** + **Groq AI (openai/gpt-oss-120b)** or native **Google Gemini 2.5 Flash Vision**.

5. **Advanced LangGraph Primitives Visualized**:
   - TypedDict State Channels & Reducers (e.g. `messages: Annotated[list, add_messages]`).
   - Conditional Edges (`add_conditional_edges`) with router logic inspection.
   - Human-in-the-Loop approval breakpoints (`interrupt_before`).
   - Presets for Hierarchical Supervisor Swarms, Self-Corrective RAG (CRAG), and Plan-and-Execute agents.

6. **1-Click Python Export**:
   - Generates 100% syntactically valid, runnable Python LangGraph 0.2+ code.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python server.py
```

### 3. Open in Browser
Navigate to **[http://localhost:3456](http://localhost:3456)** in your web browser.

---

## ⚙️ Configuration & AI Engines

- **Groq Cloud (Default)**: Preconfigured with high-speed `openai/gpt-oss-120b` for sub-second graph generation.
- **Google Gemini**: Supports free API keys from [Google AI Studio](https://aistudio.google.com/app/apikey) for native multimodal vision.
- **OpenAI**: Supports GPT-4o / GPT-4o-mini structured outputs.
