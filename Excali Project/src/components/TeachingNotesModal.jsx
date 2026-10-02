import React, { useState } from "react";

export function TeachingNotesModal({ isOpen, onClose, slideTitle, notes, onSaveNotes }) {
  const [currentNotes, setCurrentNotes] = useState(notes || "");

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 540 }}>
        <div className="modal-header">
          <div className="modal-header-info">
            <span style={{ fontSize: 24 }}>📝</span>
            <div>
              <h3>Teacher & Lecture Notes</h3>
              <p>Talking points for: <strong>{slideTitle || "Current Slide"}</strong></p>
            </div>
          </div>
          <button className="btn-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>Speaker notes (visible in Presentation Mode and exported to PPTX)</label>
            <textarea
              className="prompt-textarea"
              rows={6}
              value={currentNotes}
              onChange={(e) => setCurrentNotes(e.target.value)}
              placeholder="e.g. Introduce this concept by asking the class: 'What happens when latency spikes?' Then explain the 3 stages..."
            />
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={() => {
              onSaveNotes(currentNotes);
              onClose();
            }}
          >
            Save Notes
          </button>
        </div>
      </div>
    </div>
  );
}
