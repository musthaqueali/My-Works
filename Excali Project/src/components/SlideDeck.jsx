import React, { useState } from "react";
import "./SlideDeck.css";

export function SlideDeck({
  slides,
  activeSlideIndex,
  onSelectSlide,
  onAddSlide,
  onDuplicateSlide,
  onDeleteSlide,
  onRenameSlide,
  isOpen,
  onToggleOpen,
}) {
  const [editingIndex, setEditingIndex] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  const startRename = (index, currentTitle, e) => {
    e.stopPropagation();
    setEditingIndex(index);
    setEditTitle(currentTitle);
  };

  const saveRename = (index) => {
    if (editTitle.trim()) {
      onRenameSlide(index, editTitle.trim());
    }
    setEditingIndex(null);
  };

  return (
    <div className={`slide-deck-container ${isOpen ? "open" : "collapsed"}`}>
      <div className="slide-deck-header">
        <span className="deck-title">🎞️ Slides & Scenes ({slides.length})</span>
        <div className="deck-header-actions">
          <button className="btn-icon" onClick={onAddSlide} title="Add New Slide / Scene">
            ➕
          </button>
          <button
            className="btn-icon"
            onClick={onToggleOpen}
            title={isOpen ? "Collapse Slide Panel" : "Expand Slide Panel"}
          >
            {isOpen ? "◀" : "▶"}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="slide-list">
          {slides.map((slide, idx) => (
            <div
              key={slide.id || idx}
              className={`slide-card ${idx === activeSlideIndex ? "active" : ""}`}
              onClick={() => onSelectSlide(idx)}
            >
              <div className="slide-badge">{idx + 1}</div>
              <div className="slide-info">
                {editingIndex === idx ? (
                  <input
                    type="text"
                    value={editTitle}
                    autoFocus
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={() => saveRename(idx)}
                    onKeyDown={(e) => e.key === "Enter" && saveRename(idx)}
                    onClick={(e) => e.stopPropagation()}
                    className="slide-rename-input"
                  />
                ) : (
                  <span className="slide-title" onDoubleClick={(e) => startRename(idx, slide.title, e)}>
                    {slide.title || `Slide ${idx + 1}`}
                  </span>
                )}
                <span className="slide-meta">
                  {slide.elements ? `${slide.elements.length} elements` : "Empty"}
                </span>
              </div>

              <div className="slide-card-actions">
                <button
                  className="btn-card-action"
                  onClick={(e) => startRename(idx, slide.title, e)}
                  title="Rename slide"
                >
                  ✏️
                </button>
                <button
                  className="btn-card-action"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDuplicateSlide(idx);
                  }}
                  title="Duplicate slide"
                >
                  📋
                </button>
                {slides.length > 1 && (
                  <button
                    className="btn-card-action delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSlide(idx);
                    }}
                    title="Delete slide"
                  >
                    🗑️
                  </button>
                )}
              </div>
            </div>
          ))}

          <button className="add-slide-btn" onClick={onAddSlide}>
            <span>➕ Add New Scene</span>
          </button>
        </div>
      )}
    </div>
  );
}
