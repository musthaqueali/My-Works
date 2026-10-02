import React, { useState } from "react";
import {
  generateTeachingDiagram,
  generateTeachingSlideDeck,
  queryAIForExcalidraw,
  DEFAULT_API_KEY,
  DEFAULT_ENDPOINT,
} from "../services/aiService";
import "./AISmartModal.css";

const PRESET_TOPICS = [
  { label: "⚙️ Engineering Design Cycle", prompt: "Engineering Design Cycle and Quality Assurance" },
  { label: "🧠 AI / Machine Learning Pipeline", prompt: "Machine Learning Training and Inference Pipeline" },
  { label: "☁️ Microservices Architecture", prompt: "Cloud Microservices API Gateway and Sharded Database" },
  { label: "📈 Business Strategy Funnel", prompt: "Business Strategy Customer Acquisition and LTV Funnel" },
  { label: "🧬 Biology / Science Concept", prompt: "Cellular Energy Production and Respiration Process" },
  { label: "💻 Computer Science Data Flow", prompt: "Distributed Event-Driven Architecture with Kafka" },
];

export function AISmartModal({
  isOpen,
  onClose,
  onApplyDiagram,
  onApplySlideDeck,
  apiKey = DEFAULT_API_KEY,
  endpoint = DEFAULT_ENDPOINT,
}) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [generationType, setGenerationType] = useState("diagram"); // "diagram" or "deck"

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      alert("Please enter a topic or concept to generate.");
      return;
    }

    setLoading(true);
    setStatusMessage("AI is designing visual components and pedagogical structure...");

    try {
      if (generationType === "deck") {
        // Multi-slide teaching deck
        const deck = generateTeachingSlideDeck(prompt);
        onApplySlideDeck(deck, prompt);
        onClose();
      } else {
        // Single canvas diagram
        setStatusMessage("Generating visual teaching diagram...");
        const result = await queryAIForExcalidraw({
          prompt,
          apiKey,
          endpoint,
        });

        if (result.success && result.elements) {
          onApplyDiagram(result.elements);
        } else if (result.fallback) {
          onApplyDiagram(result.fallback);
        }
        onClose();
      }
    } catch (err) {
      console.error(err);
      // Always fallback gracefully to built-in pedagogical generator
      const fallback = generateTeachingDiagram(prompt);
      onApplyDiagram(fallback);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content ai-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-info">
            <span className="ai-sparkle">✨</span>
            <div>
              <h3>AI Teaching & Diagram Assistant</h3>
              <p>Generate visual teaching diagrams & multi-slide decks automatically</p>
            </div>
          </div>
          <button className="btn-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* Generation Target Switch */}
          <div className="mode-selector">
            <button
              className={`mode-btn ${generationType === "diagram" ? "active" : ""}`}
              onClick={() => setGenerationType("diagram")}
            >
              <span>📐 Single Canvas Diagram</span>
              <small>Adds flowcharts, architectures, or concept maps</small>
            </button>
            <button
              className={`mode-btn ${generationType === "deck" ? "active" : ""}`}
              onClick={() => setGenerationType("deck")}
            >
              <span>📊 Multi-Slide PPT Deck (4 Slides)</span>
              <small>Creates full lesson presentation with notes</small>
            </button>
          </div>

          {/* Prompt Input */}
          <div className="form-group">
            <label>What would you like to teach or visualize?</label>
            <textarea
              className="prompt-textarea"
              rows={3}
              placeholder="e.g. Mechanical Stress Analysis Pipeline, Deep Learning Training Loop, or Cloud Microservices..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  handleGenerate();
                }
              }}
            />
          </div>

          {/* Quick Presets */}
          <div className="presets-section">
            <span className="presets-label">💡 Recommended Teaching Presets:</span>
            <div className="presets-grid">
              {PRESET_TOPICS.map((item, idx) => (
                <button
                  key={idx}
                  className="preset-chip"
                  onClick={() => setPrompt(item.prompt)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* API Info Badge */}
          <div className="api-status-box">
            <span className="key-icon">🔑</span>
            <div className="api-status-text">
              <span>Connected API Key: <code>{apiKey.slice(0, 16)}...</code></span>
              <small>Optimized for professional teaching & visual explanations</small>
            </div>
          </div>

          {loading && (
            <div className="ai-loading-indicator">
              <div className="mini-spinner" />
              <span>{statusMessage}</span>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
            {loading ? "Generating..." : generationType === "deck" ? "🚀 Create 4-Slide PPT Deck" : "✨ Generate Diagram"}
          </button>
        </div>
      </div>
    </div>
  );
}
