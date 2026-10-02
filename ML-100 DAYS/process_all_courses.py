import os
import re
import json
import fitz

COURSES_META = [
    {
        "id": "ml_100",
        "vol": "VOL. 01",
        "title": "100 Days of Machine Learning",
        "subtitle": "Complete Reference & Mathematical Foundations",
        "category": "Core Machine Learning",
        "filename": "courses/100_Days_of_ML.pdf",
        "description": "2,434 pages covering classical ML, mathematical intuitions, ensemble methods (Random Forest, AdaBoost, Gradient Boost), optimization algorithms, and end-to-end MLOps lifecycle.",
        "badges": ["Machine Learning", "Mathematics", "Ensemble Learning", "Scikit-Learn"]
    },
    {
        "id": "deep_learning_100",
        "vol": "VOL. 02",
        "title": "100 Days of Deep Learning",
        "subtitle": "A Comprehensive Guide from Perceptrons to Transformers",
        "category": "Deep Learning & Neural Networks",
        "filename": "courses/100_Days_of_Deep_Learning.pdf",
        "description": "1,125 pages on neural architectures: artificial perceptrons, backpropagation mathematics, CNNs, RNNs, LSTMs, and modern Transformer self-attention mechanisms.",
        "badges": ["Neural Networks", "Backpropagation", "CNNs", "Transformers"]
    },
    {
        "id": "langchain",
        "vol": "VOL. 03",
        "title": "Generative AI with LangChain",
        "subtitle": "A Practical, End-to-End Guide to Building LLM Applications",
        "category": "Generative AI & LLMs",
        "filename": "courses/Generative_AI_with_LangChain.pdf",
        "description": "461 pages covering prompt engineering, LCEL syntax, Chains, Memory, Output Parsers, Vector Databases, and Retrieval-Augmented Generation (RAG).",
        "badges": ["LangChain", "LCEL", "RAG", "Vector DBs"]
    },
    {
        "id": "langgraph",
        "vol": "VOL. 04",
        "title": "Agentic AI using LangGraph",
        "subtitle": "From LLM Workflows to Autonomous Agents",
        "category": "Autonomous AI Agents",
        "filename": "courses/Agentic_AI_with_LangGraph.pdf",
        "description": "531 pages on stateful agentic architectures: graph states, nodes, conditional edges, multi-agent collaboration, memory persistence, and human-in-the-loop workflows.",
        "badges": ["LangGraph", "Stateful Agents", "Multi-Agent", "Human-in-the-Loop"]
    },
    {
        "id": "pytorch",
        "vol": "VOL. 05",
        "title": "PyTorch Complete Course",
        "subtitle": "Deep Learning Foundations, Tensors, Autograd & Neural Architectures",
        "category": "Deep Learning Frameworks",
        "filename": "courses/PyTorch_Complete_Course.pdf",
        "description": "304 pages covering PyTorch tensor operations, dynamic autograd computation graphs, custom datasets/dataloaders, model training loops, and deployment.",
        "badges": ["PyTorch", "Autograd", "Tensors", "Training Loops"]
    },
    {
        "id": "fastapi",
        "vol": "VOL. 06",
        "title": "FastAPI for Machine Learning",
        "subtitle": "Production-Grade API Development & Model Deployment",
        "category": "Engineering & Deployment",
        "filename": "courses/FastAPI_Complete_Course.pdf",
        "description": "365 pages of hands-on ML engineering: Pydantic data schemas, dependency injection, asynchronous endpoints, Docker containerization, and REST API deployment.",
        "badges": ["FastAPI", "Pydantic", "Model Serving", "Docker"]
    },
    {
        "id": "mcp",
        "vol": "VOL. 07",
        "title": "Model Context Protocol (MCP)",
        "subtitle": "Comprehensive Architecture Guide & Protocol Implementation",
        "category": "AI Architecture & Protocols",
        "filename": "courses/Model_Context_Protocol_MCP.pdf",
        "description": "244 pages detailing Anthropic's open Model Context Protocol. Server-client architecture, tool registration, prompt templates, resources, and IDE integration.",
        "badges": ["MCP", "Anthropic", "Tool Use", "Context Integration"]
    },
    {
        "id": "nlp",
        "vol": "VOL. 08",
        "title": "NLP Full Course & Projects",
        "subtitle": "Text Preprocessing, Embeddings, Language Models & Quora Project",
        "category": "Natural Language Processing",
        "filename": "courses/NLP_Full_Course.pdf",
        "description": "222 pages covering tokenization, TF-IDF, Word2Vec, semantic similarity, and end-to-end industrial project implementation (Quora Duplicate Question Pairs).",
        "badges": ["NLP", "Word2Vec", "TF-IDF", "Semantic Similarity"]
    },
    {
        "id": "claude_code",
        "vol": "VOL. 09",
        "title": "Claude Code Complete Guide",
        "subtitle": "AI-Assisted & Agentic Coding the Right Way",
        "category": "Agentic Coding",
        "filename": "courses/Claude_Code_Complete_Guide.pdf",
        "description": "149 pages detailing agentic coding workflows, CLI commands, context optimization, subagents, and automated code refactoring with Claude Code.",
        "badges": ["Claude Code", "Agentic Coding", "Developer Workflows"]
    },
    {
        "id": "llm_eval",
        "vol": "VOL. 10",
        "title": "LLM Evaluation Notes",
        "subtitle": "From Vibe Testing to Production-Grade Reliability",
        "category": "Evaluation & Quality",
        "filename": "courses/LLM_Evaluation_Notes.pdf",
        "description": "192 pages on measuring LLM accuracy: RAG evaluation, hallucination detection, Ragas, TruLens, LLM-as-a-judge, and CI/CD evaluation pipelines.",
        "badges": ["LLM Evaluation", "Ragas", "Hallucinations", "Production AI"]
    }
]

def clean_text(s):
    if not s:
        return ""
    # Remove control characters and clean spacing
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_native_toc(doc):
    raw_toc = doc.get_toc()
    if not raw_toc:
        return None

    chapters = []
    curr_ch = None
    curr_sec = None
    ch_lookup = []

    for lvl, title, page in raw_toc:
        title = clean_text(title)
        if not title:
            continue

        if lvl == 1:
            curr_ch = {
                "id": len(chapters) + 1,
                "title": title,
                "page": page,
                "sections": []
            }
            chapters.append(curr_ch)
            curr_sec = None
            ch_lookup.append({"id": curr_ch["id"], "title": title, "page": page})
        elif lvl == 2:
            if curr_ch is None:
                curr_ch = {"id": 1, "title": "Introduction", "page": page, "sections": []}
                chapters.append(curr_ch)
                ch_lookup.append({"id": 1, "title": "Introduction", "page": page})
            curr_sec = {
                "title": title,
                "page": page,
                "subsections": []
            }
            curr_ch["sections"].append(curr_sec)
        elif lvl == 3:
            if curr_sec is None:
                if curr_ch is None:
                    curr_ch = {"id": 1, "title": "Introduction", "page": page, "sections": []}
                    chapters.append(curr_ch)
                    ch_lookup.append({"id": 1, "title": "Introduction", "page": page})
                curr_sec = {"title": "General", "page": page, "subsections": []}
                curr_ch["sections"].append(curr_sec)
            curr_sec["subsections"].append({"title": title, "page": page})

    # Build flat items
    flat_items = []
    for ch in chapters:
        flat_items.append({"title": ch["title"], "page": ch["page"], "chapterId": ch["id"], "type": "ch"})
        for s in ch["sections"]:
            flat_items.append({"title": s["title"], "page": s["page"], "chapterId": ch["id"], "type": "sec"})
            for sub in s["subsections"]:
                flat_items.append({"title": sub["title"], "page": sub["page"], "chapterId": ch["id"], "type": "sub"})

    return {
        "chapters": chapters,
        "chapterLookup": ch_lookup,
        "flatItems": flat_items
    }

def extract_ocr_toc(doc, course_id):
    """Smart chapter and section synthesis from OCR slides/pages."""
    chapters = []
    curr_ch = None
    ch_lookup = []
    flat_items = []

    # Detect headings on each page
    pages_headings = []
    for i in range(len(doc)):
        txt = doc[i].get_text().strip()
        lines = [clean_text(l) for l in txt.split('\n') if len(clean_text(l)) > 2]
        h = ""
        if lines:
            # Pick first clean line
            first = lines[0]
            first = re.sub(r'^[o\*\-\d\.\s\?\#]+', '', first).strip()
            if len(first) > 3 and not first.lower().startswith('page') and not first.startswith('http'):
                h = first
        if not h and lines and len(lines) > 1:
            h = lines[1]
        pages_headings.append(h or f"Topic {i+1}")

    # Group into logical chapters (~10-15 pages each or at distinct title changes)
    chunk_size = 12 if len(doc) > 200 else 8
    num_chunks = max(1, (len(doc) + chunk_size - 1) // chunk_size)

    for ch_idx in range(num_chunks):
        start_p = ch_idx * chunk_size
        end_p = min(len(doc), (ch_idx + 1) * chunk_size)
        ch_title = pages_headings[start_p] if pages_headings[start_p] else f"Section {ch_idx+1}"
        # Truncate if too long
        if len(ch_title) > 65:
            ch_title = ch_title[:62] + "..."

        curr_ch = {
            "id": ch_idx + 1,
            "title": ch_title,
            "page": start_p + 1,
            "sections": []
        }
        ch_lookup.append({"id": curr_ch["id"], "title": ch_title, "page": start_p + 1})
        flat_items.append({"title": ch_title, "page": start_p + 1, "chapterId": curr_ch["id"], "type": "ch"})

        # Add individual page topics as sections
        for p in range(start_p, end_p):
            sec_title = pages_headings[p]
            if sec_title and sec_title != ch_title:
                if len(sec_title) > 60:
                    sec_title = sec_title[:57] + "..."
                curr_ch["sections"].append({
                    "title": sec_title,
                    "page": p + 1,
                    "subsections": []
                })
                flat_items.append({"title": sec_title, "page": p + 1, "chapterId": curr_ch["id"], "type": "sec"})

        chapters.append(curr_ch)

    return {
        "chapters": chapters,
        "chapterLookup": ch_lookup,
        "flatItems": flat_items
    }

def main():
    print("Processing all 10 courses...")
    courses_catalog = []
    courses_toc = {}

    total_pages_all = 0
    total_topics_all = 0

    for meta in COURSES_META:
        cid = meta["id"]
        fpath = meta["filename"]
        if not os.path.exists(fpath):
            print(f"Warning: File not found: {fpath}")
            continue

        doc = fitz.open(fpath)
        page_count = len(doc)
        total_pages_all += page_count

        # Extract TOC
        toc_result = extract_native_toc(doc)
        if not toc_result or len(toc_result["chapters"]) < 2:
            print(f"  [{cid}] Using smart OCR heading extractor ({page_count} pages)...")
            toc_result = extract_ocr_toc(doc, cid)
        else:
            print(f"  [{cid}] Extracted native TOC: {len(toc_result['chapters'])} chapters, {len(toc_result['flatItems'])} topics ({page_count} pages).")

        topic_count = len(toc_result["flatItems"])
        total_topics_all += topic_count

        course_item = dict(meta)
        course_item["pages"] = page_count
        course_item["topics"] = topic_count
        course_item["chaptersCount"] = len(toc_result["chapters"])
        courses_catalog.append(course_item)

        courses_toc[cid] = toc_result

    print("\nSummary:")
    print(f"Total Courses: {len(courses_catalog)}")
    print(f"Total Pages Across Library: {total_pages_all:,}")
    print(f"Total Topics: {total_topics_all:,}")

    # Output courses_data.js
    js_content = f"""// Auto-generated Multi-Course AI & ML Library Catalog & TOC Data
const COURSES_CATALOG = {json.dumps(courses_catalog, ensure_ascii=False, indent=2)};
const COURSES_TOC = {json.dumps(courses_toc, ensure_ascii=False)};
"""

    with open("courses_data.js", "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Saved courses_data.js successfully ({os.path.getsize('courses_data.js') / (1024*1024):.2f} MB).")

if __name__ == "__main__":
    main()
