import pptxgen from "pptxgenjs";
import jsPDF from "jspdf";
import { exportToBlob } from "@excalidraw/excalidraw";

// Convert an array of Excalidraw elements to a Base64 image
export async function elementsToBase64(elements, appState = {}, files = {}) {
  try {
    const blob = await exportToBlob({
      elements: elements.filter((el) => !el.isDeleted),
      mimeType: "image/png",
      appState: {
        ...appState,
        exportWithDarkMode: false,
        exportBackground: true,
        viewBackgroundColor: "#ffffff",
      },
      files,
    });

    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch (err) {
    console.error("Failed to render elements to base64:", err);
    return null;
  }
}

// Export All Slides as a Native PowerPoint Presentation (.pptx)
export async function exportSlidesToPPTX(slides, presentationTitle = "Professional Teaching Presentation") {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.title = presentationTitle;

  // Title Slide
  const titleSlide = pres.addSlide();
  titleSlide.background = { color: "1E1B4B" }; // Deep indigo
  titleSlide.addText(presentationTitle, {
    x: 0.8,
    y: 2.2,
    w: "85%",
    h: 1.5,
    fontSize: 36,
    color: "FFFFFF",
    bold: true,
    fontFace: "Arial",
  });
  titleSlide.addText("Generated with Excalidraw AI & Teaching Studio", {
    x: 0.8,
    y: 3.8,
    w: "85%",
    h: 0.8,
    fontSize: 18,
    color: "A5B4FC",
    fontFace: "Arial",
  });

  // Render each slide from canvas
  for (let i = 0; i < slides.length; i++) {
    const slideItem = slides[i];
    const pptSlide = pres.addSlide();

    // Top Header Banner
    pptSlide.addText(slideItem.title || `Slide ${i + 1}`, {
      x: 0.6,
      y: 0.4,
      w: "90%",
      h: 0.6,
      fontSize: 22,
      color: "0F172A",
      bold: true,
      fontFace: "Arial",
    });

    // Add Canvas Image if elements exist
    if (slideItem.elements && slideItem.elements.length > 0) {
      const base64Data = await elementsToBase64(slideItem.elements);
      if (base64Data) {
        pptSlide.addImage({
          data: base64Data,
          x: 0.6,
          y: 1.2,
          w: 8.8,
          h: 4.8,
          sizing: { type: "contain", w: 8.8, h: 4.8 },
        });
      }
    }

    // Add Speaker/Teaching Notes if any
    if (slideItem.notes) {
      pptSlide.addNotes(slideItem.notes);
    }
  }

  // Save the PowerPoint presentation file
  const filename = `${presentationTitle.replace(/[^a-zA-Z0-9_-]/g, "_")}.pptx`;
  await pres.writeFile({ fileName: filename });
  return filename;
}

// Export All Slides as a PDF Presentation Document
export async function exportSlidesToPDF(slides, presentationTitle = "Excalidraw-Presentation") {
  const doc = new jsPDF({
    orientation: "landscape",
    unit: "in",
    format: [11, 6.2], // 16:9 approx
  });

  for (let i = 0; i < slides.length; i++) {
    const slideItem = slides[i];
    if (i > 0) doc.addPage([11, 6.2], "landscape");

    // Title
    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.setTextColor(30, 41, 59);
    doc.text(slideItem.title || `Slide ${i + 1}`, 0.6, 0.7);

    // Canvas Image
    if (slideItem.elements && slideItem.elements.length > 0) {
      const base64Data = await elementsToBase64(slideItem.elements);
      if (base64Data) {
        doc.addImage(base64Data, "PNG", 0.6, 1.0, 9.8, 4.8);
      }
    }
  }

  const filename = `${presentationTitle.replace(/[^a-zA-Z0-9_-]/g, "_")}.pdf`;
  doc.save(filename);
  return filename;
}
