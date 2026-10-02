import React, { useState, useEffect, useRef } from "react";
import confetti from "canvas-confetti";
import { elementsToBase64, exportSlidesToPPTX } from "../services/exportService";
import "./PresentationModal.css";

export function PresentationModal({ slides, initialSlideIndex = 0, onClose, onExportPPTX }) {
  const [currentIndex, setCurrentIndex] = useState(initialSlideIndex);
  const [laserActive, setLaserActive] = useState(false);
  const [laserPos, setLaserPos] = useState({ x: -100, y: -100 });
  const [showNotes, setShowNotes] = useState(false);
  const [slideImages, setSlideImages] = useState({});
  const [loading, setLoading] = useState(true);
  const containerRef = useRef(null);

  // Pre-render slide snapshots for instant smooth playback
  useEffect(() => {
    let isMounted = true;
    async function loadAllSlides() {
      setLoading(true);
      const images = {};
      for (let i = 0; i < slides.length; i++) {
        if (slides[i].elements && slides[i].elements.length > 0) {
          images[i] = await elementsToBase64(slides[i].elements);
        }
      }
      if (isMounted) {
        setSlideImages(images);
        setLoading(false);
      }
    }
    loadAllSlides();
    return () => {
      isMounted = false;
    };
  }, [slides]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") {
        e.preventDefault();
        goNext();
      } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        goPrev();
      } else if (e.key === "Escape") {
        onClose();
      } else if (e.key === "l" || e.key === "L") {
        setLaserActive((prev) => !prev);
      } else if (e.key === "n" || e.key === "N") {
        setShowNotes((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, slides.length]);

  const goNext = () => {
    if (currentIndex < slides.length - 1) {
      const nextIdx = currentIndex + 1;
      setCurrentIndex(nextIdx);
      if (nextIdx === slides.length - 1) {
        confetti({ particleCount: 70, spread: 60, origin: { y: 0.8 } });
      }
    }
  };

  const goPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleMouseMove = (e) => {
    if (laserActive && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setLaserPos({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  const currentSlide = slides[currentIndex] || {};

  return (
    <div
      className="presentation-overlay"
      ref={containerRef}
      onMouseMove={handleMouseMove}
      style={{ cursor: laserActive ? "none" : "default" }}
    >
      {/* Laser Pointer Dot */}
      {laserActive && (
        <div
          className="laser-pointer"
          style={{ left: `${laserPos.x}px`, top: `${laserPos.y}px` }}
        />
      )}

      {/* Top Floating Controls */}
      <div className="presentation-top-bar">
        <div className="slide-counter-badge">
          <span>
            Slide {currentIndex + 1} of {slides.length}
          </span>
          <span className="slide-title-preview">{currentSlide.title || "Untitled Slide"}</span>
        </div>

        <div className="presentation-top-actions">
          <button
            className={`btn-pres ${laserActive ? "active" : ""}`}
            onClick={() => setLaserActive((prev) => !prev)}
            title="Toggle Laser Pointer (Press 'L')"
          >
            🔴 Laser Pointer {laserActive ? "ON" : "OFF"}
          </button>
          <button
            className={`btn-pres ${showNotes ? "active" : ""}`}
            onClick={() => setShowNotes((prev) => !prev)}
            title="Teaching / Speaker Notes (Press 'N')"
          >
            📝 Notes
          </button>
          <button
            className="btn-pres"
            onClick={onExportPPTX}
            title="Download as PowerPoint Presentation"
          >
            📊 Export .PPTX
          </button>
          <button className="btn-pres close" onClick={onClose} title="Exit Presentation (Esc)">
            ✕ Exit
          </button>
        </div>
      </div>

      {/* Center Slide Stage */}
      <div className="presentation-stage">
        {loading ? (
          <div className="pres-loading">
            <div className="spinner" />
            <span>Preparing Presentation Slides...</span>
          </div>
        ) : slideImages[currentIndex] ? (
          <img
            src={slideImages[currentIndex]}
            alt={currentSlide.title || "Slide"}
            className="slide-display-img"
          />
        ) : (
          <div className="empty-slide-placeholder">
            <h3>Canvas is empty on this slide</h3>
            <p>Add drawings, shapes, or diagrams on the whiteboard to present.</p>
          </div>
        )}
      </div>

      {/* Speaker Notes Overlay */}
      {showNotes && (
        <div className="speaker-notes-panel">
          <h4>👨‍🏫 Teaching Notes & Lecture Talking Points:</h4>
          <p>{currentSlide.notes || "No notes entered for this slide yet. You can add lecture notes in the whiteboard."}</p>
        </div>
      )}

      {/* Bottom Floating Control Bar */}
      <div className="presentation-bottom-bar">
        <button
          className="btn-nav"
          onClick={goPrev}
          disabled={currentIndex === 0}
          title="Previous Slide (Left Arrow)"
        >
          ◀ Prev
        </button>

        <div className="progress-dots">
          {slides.map((_, idx) => (
            <button
              key={idx}
              className={`dot ${idx === currentIndex ? "active" : ""}`}
              onClick={() => setCurrentIndex(idx)}
              title={`Go to Slide ${idx + 1}`}
            />
          ))}
        </div>

        <button
          className="btn-nav"
          onClick={goNext}
          disabled={currentIndex === slides.length - 1}
          title="Next Slide (Right Arrow / Space)"
        >
          Next ▶
        </button>
      </div>
    </div>
  );
}
