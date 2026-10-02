import React, { useState, useEffect, useRef } from "react";
import { Excalidraw, serializeAsJSON, convertToExcalidrawElements } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
import "./App.css";

import { welcomeDiagram, architectureTemplate, flowchartTemplate } from "./templates";
import { SlideDeck } from "./components/SlideDeck";
import { PresentationModal } from "./components/PresentationModal";
import { AISmartModal } from "./components/AISmartModal";
import { SettingsModal } from "./components/SettingsModal";
import { TeachingNotesModal } from "./components/TeachingNotesModal";
import { exportSlidesToPPTX, exportSlidesToPDF } from "./services/exportService";
import { DEFAULT_API_KEY, DEFAULT_ENDPOINT, generateId } from "./services/aiService";

const STORAGE_PROJECT_KEY = "excalidraw_pro_teaching_project";
const STORAGE_CONFIG_KEY = "excalidraw_pro_config";

export default function App() {
  const [excalidrawAPI, setExcalidrawAPI] = useState(null);
  const [theme, setTheme] = useState("light");
  const [slideDeckOpen, setSlideDeckOpen] = useState(true);

  // Slides State (Unlimited Scenes & Multi-Page Presentations)
  const [slides, setSlides] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_PROJECT_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed?.slides && parsed.slides.length > 0) {
          return parsed.slides;
        }
      }
    } catch (e) {
      console.warn("Could not load saved slides:", e);
    }
    // Default professional starting deck
    return [
      {
        id: generateId("slide"),
        title: "1. Lesson Overview & Objectives",
        notes: "Welcome students/colleagues. Cover foundational principles and learning objectives.",
        elements: welcomeDiagram,
      },
      {
        id: generateId("slide"),
        title: "2. Technical Architecture & Flow",
        notes: "Explain data flow, message queues, and component communication.",
        elements: architectureTemplate,
      },
      {
        id: generateId("slide"),
        title: "3. Decision Logic & Quality Gate",
        notes: "Step through execution pipeline and verify standard operating procedures.",
        elements: flowchartTemplate,
      },
    ];
  });

  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [savedStatus, setSavedStatus] = useState("Saved");

  // Modals
  const [isPresMode, setIsPresMode] = useState(false);
  const [isAIModalOpen, setIsAIModalOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isNotesOpen, setIsNotesOpen] = useState(false);

  // Settings
  const [config, setConfig] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_CONFIG_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return { apiKey: DEFAULT_API_KEY, endpoint: DEFAULT_ENDPOINT, model: "gpt-4o-mini" };
  });

  const fileInputRef = useRef(null);

  const saveTimeoutRef = useRef(null);

  // Synchronize current canvas changes into active slide with debouncing
  const handleCanvasChange = (elements, appState) => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    saveTimeoutRef.current = setTimeout(() => {
      const activeElements = elements.filter((el) => !el.isDeleted);
      setSlides((prevSlides) => {
        const updated = [...prevSlides];
        if (updated[activeSlideIndex]) {
          updated[activeSlideIndex] = {
            ...updated[activeSlideIndex],
            elements: activeElements,
          };
        }
        try {
          localStorage.setItem(STORAGE_PROJECT_KEY, JSON.stringify({ slides: updated }));
        } catch (e) {
          console.warn("Storage quota limit reached");
        }
        return updated;
      });
      setSavedStatus("Saved");
    }, 400);
  };

  // Switch Active Slide
  const handleSelectSlide = (targetIndex) => {
    if (targetIndex === activeSlideIndex || !excalidrawAPI) return;

    // 1. Capture current elements from canvas into current slide
    const currentElements = excalidrawAPI.getSceneElements().filter((el) => !el.isDeleted);
    const updatedSlides = [...slides];
    updatedSlides[activeSlideIndex].elements = currentElements;

    // 2. Switch to target slide
    const targetSlide = updatedSlides[targetIndex];
    setActiveSlideIndex(targetIndex);
    setSlides(updatedSlides);

    // 3. Render target slide elements
    excalidrawAPI.updateScene({
      elements: targetSlide.elements || [],
      commitToHistory: true,
    });
    excalidrawAPI.scrollToContent();
  };

  // Add New Slide
  const handleAddSlide = () => {
    const newSlide = {
      id: generateId("slide"),
      title: `${slides.length + 1}. New Teaching Scene`,
      notes: "",
      elements: [],
    };
    const newSlides = [...slides, newSlide];
    setSlides(newSlides);
    handleSelectSlide(newSlides.length - 1);
  };

  // Duplicate Slide
  const handleDuplicateSlide = (index) => {
    const source = slides[index];
    const duplicated = {
      id: generateId("slide"),
      title: `${source.title} (Copy)`,
      notes: source.notes,
      elements: JSON.parse(JSON.stringify(source.elements || [])),
    };
    const newSlides = [...slides];
    newSlides.splice(index + 1, 0, duplicated);
    setSlides(newSlides);
    handleSelectSlide(index + 1);
  };

  // Delete Slide
  const handleDeleteSlide = (index) => {
    if (slides.length <= 1) return;
    if (window.confirm(`Delete "${slides[index].title}"?`)) {
      const newSlides = slides.filter((_, i) => i !== index);
      const nextIndex = Math.min(activeSlideIndex, newSlides.length - 1);
      setSlides(newSlides);
      setActiveSlideIndex(nextIndex);
      if (excalidrawAPI && newSlides[nextIndex]) {
        excalidrawAPI.updateScene({
          elements: newSlides[nextIndex].elements || [],
          commitToHistory: true,
        });
      }
    }
  };

  // Rename Slide
  const handleRenameSlide = (index, newTitle) => {
    setSlides((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], title: newTitle };
      localStorage.setItem(STORAGE_PROJECT_KEY, JSON.stringify({ slides: updated }));
      return updated;
    });
  };

  // Update Notes
  const handleSaveNotes = (notes) => {
    setSlides((prev) => {
      const updated = [...prev];
      updated[activeSlideIndex] = { ...updated[activeSlideIndex], notes };
      localStorage.setItem(STORAGE_PROJECT_KEY, JSON.stringify({ slides: updated }));
      return updated;
    });
  };

  // Apply AI Diagram to Current Canvas
  const handleApplyAIDiagram = (newElements) => {
    if (!excalidrawAPI) return;
    const current = excalidrawAPI.getSceneElements().filter((el) => !el.isDeleted);
    const combined = [...current, ...newElements];
    
    // Update Scene
    excalidrawAPI.updateScene({
      elements: combined,
      commitToHistory: true,
    });

    // Zoom and center into view
    setTimeout(() => {
      try {
        excalidrawAPI.scrollToContent(combined, { fitToViewport: true, viewportZoomFactor: 0.85 });
      } catch (e) {
        console.warn("Scroll to content error:", e);
      }
    }, 60);

    // Save state immediately
    setSlides((prev) => {
      const updated = [...prev];
      if (updated[activeSlideIndex]) {
        updated[activeSlideIndex] = {
          ...updated[activeSlideIndex],
          elements: combined,
        };
      }
      try {
        localStorage.setItem(STORAGE_PROJECT_KEY, JSON.stringify({ slides: updated }));
      } catch (e) {}
      return updated;
    });
  };

  // Apply AI Generated Multi-Slide Deck
  const handleApplyAISlideDeck = (newDeck, topic) => {
    setSlides(newDeck);
    setActiveSlideIndex(0);
    try {
      localStorage.setItem(STORAGE_PROJECT_KEY, JSON.stringify({ slides: newDeck }));
    } catch (e) {}
    if (excalidrawAPI && newDeck[0]) {
      excalidrawAPI.updateScene({
        elements: newDeck[0].elements || [],
        commitToHistory: true,
      });
      setTimeout(() => {
        try {
          excalidrawAPI.scrollToContent(newDeck[0].elements || [], { fitToViewport: true, viewportZoomFactor: 0.85 });
        } catch (e) {}
      }, 60);
    }
  };

  // Insert Stamp Annotations for Teaching
  const insertTeachingStamp = (text, bgColor, strokeColor) => {
    if (!excalidrawAPI) return;
    const elements = convertToExcalidrawElements([
      {
        type: "rectangle",
        x: 200,
        y: 200,
        width: 250,
        height: 60,
        backgroundColor: bgColor,
        strokeColor: strokeColor,
        fillStyle: "solid",
        roundness: { type: 3 },
        label: {
          text: text,
          fontSize: 16,
          textAlign: "center",
          verticalAlign: "middle",
        },
      },
    ]);
    handleApplyAIDiagram(elements);
  };

  // Export to PowerPoint (.pptx)
  const handleExportPPTX = async () => {
    try {
      setSavedStatus("Generating .PPTX...");
      await exportSlidesToPPTX(slides, "Teaching_Presentation_Deck");
      setSavedStatus("Saved");
    } catch (err) {
      alert("Error generating PowerPoint presentation: " + err.message);
      setSavedStatus("Error");
    }
  };

  // Export to PDF
  const handleExportPDF = async () => {
    try {
      setSavedStatus("Generating PDF...");
      await exportSlidesToPDF(slides, "Teaching_Presentation");
      setSavedStatus("Saved");
    } catch (err) {
      alert("Error generating PDF: " + err.message);
      setSavedStatus("Error");
    }
  };

  // Export Full Project JSON Bundle
  const handleExportBundle = () => {
    const dataStr = JSON.stringify({ slides, exportDate: new Date().toISOString() }, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `teaching-deck-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Import Project JSON Bundle
  const handleImportBundle = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target.result);
        if (parsed.slides && Array.isArray(parsed.slides)) {
          setSlides(parsed.slides);
          setActiveSlideIndex(0);
          if (excalidrawAPI) {
            excalidrawAPI.updateScene({ elements: parsed.slides[0].elements || [] });
          }
        } else if (parsed.elements) {
          // Single excalidraw file loaded into current slide
          handleApplyAIDiagram(parsed.elements);
        }
      } catch (err) {
        alert("Invalid project file format.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const currentSlide = slides[activeSlideIndex] || {};

  return (
    <div className={`app-container ${theme}`}>
      {/* Top Application Bar */}
      <header className="app-header">
        <div className="header-left">
          <button
            className="btn-toggle-deck"
            onClick={() => setSlideDeckOpen(!slideDeckOpen)}
            title="Toggle Slide & Scene Manager"
          >
            🎞️ {slideDeckOpen ? "Hide Scenes" : "Show Scenes"}
          </button>

          <div className="logo-badge">
            <span className="logo-icon">🎨</span>
            <span className="logo-title">Excalidraw Teaching & AI Studio</span>
          </div>

          <span className="save-status">
            <span className={`status-dot ${savedStatus === "Saved" ? "active" : ""}`} />
            {savedStatus}
          </span>
        </div>

        <div className="header-actions">
          {/* AI Generation Button */}
          <button
            className="btn btn-ai"
            onClick={() => setIsAIModalOpen(true)}
            title="Generate diagrams and slide decks automatically using AI"
          >
            ✨ AI Assistant
          </button>

          {/* Presentation Mode */}
          <button
            className="btn btn-present"
            onClick={() => setIsPresMode(true)}
            title="Start Fullscreen Presentation Mode (PPT Slideshow with Laser Pointer)"
          >
            📽️ Present (PPT Mode)
          </button>

          {/* Teacher Notes */}
          <button
            className="btn btn-secondary"
            onClick={() => setIsNotesOpen(true)}
            title="Lecture Talking Points & Notes for Current Slide"
          >
            📝 Notes
          </button>

          {/* Teaching Annotations / Stencils */}
          <div className="dropdown">
            <button className="btn btn-secondary">
              🏷️ Stamps ▾
            </button>
            <div className="dropdown-menu">
              <button onClick={() => insertTeachingStamp("⭐ KEY PRINCIPLE", "#dbeafe", "#1d4ed8")}>
                ⭐ Key Principle
              </button>
              <button onClick={() => insertTeachingStamp("⚠️ EXAM / RISK POINT", "#fee2e2", "#b91c1c")}>
                ⚠️ Exam / Risk Point
              </button>
              <button onClick={() => insertTeachingStamp("✅ VERIFIED / APPROVED", "#d1fae5", "#047857")}>
                ✅ Verified / Approved
              </button>
              <button onClick={() => insertTeachingStamp("💡 CLASS DISCUSSION", "#fef3c7", "#b45309")}>
                💡 Class Discussion
              </button>
            </div>
          </div>

          {/* Export Dropdown */}
          <div className="dropdown">
            <button className="btn btn-secondary">
              📤 Export ▾
            </button>
            <div className="dropdown-menu">
              <button onClick={handleExportPPTX}>
                📊 Export to PowerPoint (.pptx)
              </button>
              <button onClick={handleExportPDF}>
                📄 Export to PDF Presentation
              </button>
              <button onClick={handleExportBundle}>
                💾 Save Project Bundle (.json)
              </button>
            </div>
          </div>

          {/* Open / Import */}
          <button
            className="btn btn-secondary"
            onClick={() => fileInputRef.current?.click()}
            title="Open saved presentation or diagram"
          >
            📂 Open
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImportBundle}
            accept=".json,.excalidraw"
            style={{ display: "none" }}
          />

          {/* Settings */}
          <button
            className="btn btn-secondary"
            onClick={() => setIsSettingsOpen(true)}
            title="Configure AI API Key & Endpoints"
          >
            ⚙️
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="workspace-layout">
        {/* Slide & Scene Management Drawer */}
        <SlideDeck
          slides={slides}
          activeSlideIndex={activeSlideIndex}
          onSelectSlide={handleSelectSlide}
          onAddSlide={handleAddSlide}
          onDuplicateSlide={handleDuplicateSlide}
          onDeleteSlide={handleDeleteSlide}
          onRenameSlide={handleRenameSlide}
          isOpen={slideDeckOpen}
          onToggleOpen={() => setSlideDeckOpen(!slideDeckOpen)}
        />

        {/* Whiteboard Canvas */}
        <main
          className="canvas-wrapper"
          style={{
            marginLeft: slideDeckOpen ? 240 : 44,
            transition: "margin-left 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        >
          <Excalidraw
            excalidrawAPI={(api) => setExcalidrawAPI(api)}
            initialData={{
              elements: currentSlide.elements || [],
              appState: { theme },
            }}
            onChange={handleCanvasChange}
            gridModeEnabled={true}
            zenModeEnabled={false}
          />
        </main>
      </div>

      {/* Presentation Fullscreen Modal */}
      {isPresMode && (
        <PresentationModal
          slides={slides}
          initialSlideIndex={activeSlideIndex}
          onClose={() => setIsPresMode(false)}
          onExportPPTX={handleExportPPTX}
        />
      )}

      {/* AI Assistant Modal */}
      <AISmartModal
        isOpen={isAIModalOpen}
        onClose={() => setIsAIModalOpen(false)}
        onApplyDiagram={handleApplyAIDiagram}
        onApplySlideDeck={handleApplyAISlideDeck}
        apiKey={config.apiKey}
        endpoint={config.endpoint}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        apiKey={config.apiKey}
        endpoint={config.endpoint}
        onSaveSettings={(newCfg) => {
          setConfig(newCfg);
          localStorage.setItem(STORAGE_CONFIG_KEY, JSON.stringify(newCfg));
        }}
      />

      {/* Slide Notes Modal */}
      <TeachingNotesModal
        isOpen={isNotesOpen}
        onClose={() => setIsNotesOpen(false)}
        slideTitle={currentSlide.title}
        notes={currentSlide.notes}
        onSaveNotes={handleSaveNotes}
      />
    </div>
  );
}
