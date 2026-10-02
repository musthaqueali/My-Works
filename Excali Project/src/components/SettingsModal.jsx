import React, { useState } from "react";
import { DEFAULT_API_KEY, DEFAULT_ENDPOINT } from "../services/aiService";

export function SettingsModal({ isOpen, onClose, apiKey, endpoint, onSaveSettings }) {
  const [key, setKey] = useState(apiKey || DEFAULT_API_KEY);
  const [url, setUrl] = useState(endpoint || DEFAULT_ENDPOINT);
  const [model, setModel] = useState("gpt-4o-mini");

  if (!isOpen) return null;

  const handleSave = () => {
    onSaveSettings({ apiKey: key.trim(), endpoint: url.trim(), model });
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 520 }}>
        <div className="modal-header">
          <div className="modal-header-info">
            <span style={{ fontSize: 24 }}>⚙️</span>
            <div>
              <h3>AI & Workspace Configuration</h3>
              <p>Configure your LLM API and teaching environment</p>
            </div>
          </div>
          <button className="btn-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>API Key (LLM / OpenAI / Proxy)</label>
            <input
              type="text"
              className="prompt-textarea"
              style={{ height: 42, padding: "8px 12px" }}
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="Paste your API key here..."
            />
            <small style={{ color: "#64748b", marginTop: 4, display: "block" }}>
              Pre-configured with your provided API key.
            </small>
          </div>

          <div className="form-group">
            <label>API Endpoint Base URL</label>
            <input
              type="text"
              className="prompt-textarea"
              style={{ height: 42, padding: "8px 12px" }}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://api.openai.com/v1/chat/completions"
            />
            <small style={{ color: "#64748b", marginTop: 4, display: "block" }}>
              Supports OpenAI, Azure, LiteLLM, or custom enterprise gateways.
            </small>
          </div>

          <div className="form-group">
            <label>Model Identifier</label>
            <select
              className="prompt-textarea"
              style={{ height: 42, padding: "8px 12px" }}
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              <option value="gpt-4o-mini">gpt-4o-mini (Fast & Recommended)</option>
              <option value="gpt-4o">gpt-4o (High Reasoning)</option>
              <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
              <option value="custom">Custom / Gateway Managed</option>
            </select>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
