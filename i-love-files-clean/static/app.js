/**

 * 'I LOVE FILES' - Clean & Simple Frontend

 * Direct, fast, zero fluff.

 */



function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatBytes(bytes) {
  if (!bytes || isNaN(bytes) || bytes <= 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

let globalCatalog = {};

let selectedConvertFile = null;

let selectedConvertFiles = [];

let selectedResizeFile = null;

let activeResizeType = "pdf";

let inspectedPdfPageCount = 1;



let selectedPlotFiles = [];

let selectedCustomCtb = null;



document.addEventListener("DOMContentLoaded", async () => {

  initTheme();

  if (window.location.protocol === 'file:') {

    const banner = document.createElement('div');

    banner.style.cssText = "background: #fff3cd; color: #856404; padding: 12px 20px; text-align: center; font-weight: 500; font-size: 0.9rem; border-bottom: 1px solid #ffeeba; position: sticky; top: 0; z-index: 9999;";

    banner.innerHTML = "⚠️ <strong>Notice:</strong> You opened index.html directly from file explorer. For real account creation, Google Sign-In, and conversions, please launch <code>run_app.bat</code> and open <a href='http://localhost:8000' style='color:#0d6efd;font-weight:700;'>http://localhost:8000</a>.";

    document.body.insertBefore(banner, document.body.firstChild);

  }

  clearSearchInputAutofill();

  await fetchCatalog();

  await initAuth();

  setupDragAndDrop();

  initLandingStudio();
  updateCloudEgressMetric();
  lucide.createIcons();

  const navTrack = document.querySelector('.nav-tab-container');
  if (navTrack) {
    navTrack.addEventListener('wheel', (e) => {
      if (e.deltaY !== 0) {
        e.preventDefault();
        navTrack.scrollLeft += e.deltaY;
      }
    }, { passive: false });
  }
});



function clearSearchInputAutofill() {

  const searchInput = document.getElementById('hub-search-input');

  if (searchInput) {

    if (searchInput.value && (searchInput.value.includes('@') || searchInput.value.includes('.com') || searchInput.value.trim() === 'musthaqueali42@gmail.com')) {

      searchInput.value = '';

      if (typeof filterToolCards === 'function') filterToolCards('');

    }

  }

}



window.addEventListener('pageshow', clearSearchInputAutofill);

window.addEventListener('load', () => {

  clearSearchInputAutofill();

  setTimeout(clearSearchInputAutofill, 100);

  setTimeout(clearSearchInputAutofill, 400);

  setTimeout(clearSearchInputAutofill, 1000);

});



async function fetchCatalog() {

  try {

    const res = await fetch("/api/formats");

    const data = await res.json();

    globalCatalog = data.catalog || {};

  } catch (err) {

    console.error("Failed to load catalog:", err);

  }

}



// -------------------------------------------------------------

// Tab Switching

// -------------------------------------------------------------

function switchTab(tabId) {
  ["convert", "plot", "merge", "resize", "pcml"].forEach(hideError);
  ["convert", "plot", "merge", "resize", "images", "chat", "ai", "faq", "pcml"].forEach(t => {
    const view = document.getElementById(`view-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (view) {
      view.style.display = (t === tabId) ? "block" : "none";
      view.classList.toggle("active", t === tabId);
    }
    if (btn) btn.classList.toggle("active", t === tabId);
  });
  if (tabId === 'chat') {
    if (typeof initClaudeStudio === 'function') initClaudeStudio();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else if (tabId === 'ai') {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else if (tabId === 'pcml') {
    if (typeof initPcmlStudio === 'function') initPcmlStudio();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  if (window.lucide) lucide.createIcons();
}



function switchResizeSubTab(type) {

  activeResizeType = type;

  ["pdf", "image", "video"].forEach(st => {

    const btn = document.getElementById(`resize-subtab-${st}`);

    const ctrl = document.getElementById(`controls-${st}`);

    if (btn) btn.classList.toggle("active", st === type);

    if (ctrl) ctrl.style.display = (st === type) ? "block" : "none";

  });



  const title = document.getElementById("resize-drop-title");

  const desc = document.getElementById("resize-drop-desc");

  if (type === "pdf") {

    title.innerText = "Choose PDF to resize";

    desc.innerText = "Normalizes page dimensions (A4, Letter) and compresses file size";

  } else if (type === "image") {

    title.innerText = "Choose Image to resize";

    desc.innerText = "Custom width, height, and quality compression (PNG, JPG, WebP)";

  } else if (type === "video") {

    title.innerText = "Choose Video to downscale";

    desc.innerText = "Scales 4K/1080p to 720p/480p and compresses bitrate (MP4, MKV, MOV)";

  }

  lucide.createIcons();

}



// -------------------------------------------------------------

// Drag and Drop

// -------------------------------------------------------------

function setupDragAndDrop() {

  const convertZone = document.getElementById("convert-dropzone");

  const plotZone = document.getElementById("plot-dropzone");

  const mergeZone = document.getElementById("merge-dropzone");

  const resizeZone = document.getElementById("resize-dropzone");



  [convertZone, plotZone, mergeZone, resizeZone].forEach(zone => {

    if (!zone) return;

    ['dragenter', 'dragover'].forEach(evt => {

      zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.add('dragover'); });

    });

    ['dragleave', 'drop'].forEach(evt => {

      zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.remove('dragover'); });

    });

  });



  if (convertZone) {

    convertZone.addEventListener('drop', (e) => {

      if (e.dataTransfer.files.length) handleConvertFileSelect(e.dataTransfer.files);

    });

  }

  if (plotZone) {

    plotZone.addEventListener('drop', (e) => {

      if (e.dataTransfer.files.length) handlePlotFilesSelect(e.dataTransfer.files);

    });

  }

  if (mergeZone) {

    mergeZone.addEventListener('drop', (e) => {

      if (e.dataTransfer.files.length) handleMergeFilesSelect(e.dataTransfer.files);

    });

  }

  if (resizeZone) {

    resizeZone.addEventListener('drop', (e) => {

      if (e.dataTransfer.files.length) handleResizeFileSelect(e.dataTransfer.files);

    });

  }

}



// -------------------------------------------------------------

// UI Error Notifications

// -------------------------------------------------------------

function showError(prefix, message) {

  const banner = document.getElementById(`${prefix}-error-banner`);

  const text = document.getElementById(`${prefix}-error-text`);

  if (banner && text) {

    text.innerText = message;

    banner.style.display = "flex";

    lucide.createIcons();

  }

}



function hideError(prefix) {

  const banner = document.getElementById(`${prefix}-error-banner`);

  if (banner) banner.style.display = "none";

}



// -------------------------------------------------------------

// Convert Logic

// -------------------------------------------------------------

const DIRECT_PDF_TOOLS = [

  'word-to-pdf', 'excel-to-pdf', 'ppt-to-pdf', 'jpg-to-pdf', 'png-to-pdf',

  'heic-to-pdf', 'autocad-to-pdf', 'openoffice-to-pdf', 'ebook-to-pdf',

  'iwork-to-pdf', 'publisher-to-pdf', 'dicom-to-pdf'

];



const DIRECT_TARGET_MAP = {

  'word-to-pdf': 'pdf',

  'excel-to-pdf': 'pdf',

  'ppt-to-pdf': 'pdf',

  'jpg-to-pdf': 'pdf',

  'png-to-pdf': 'pdf',

  'heic-to-pdf': 'pdf',

  'autocad-to-pdf': 'pdf',

  'openoffice-to-pdf': 'pdf',

  'ebook-to-pdf': 'pdf',

  'iwork-to-pdf': 'pdf',

  'publisher-to-pdf': 'pdf',

  'dicom-to-pdf': 'pdf',

  'pdf-to-word': 'docx',

  'pdf-to-excel': 'xlsx',

  'pdf-to-pptx': 'pptx',

  'pdf-to-jpg': 'jpg',

  'pdf-to-png': 'png',

  'pdf-to-pdfa': 'pdf',

  'dwg-to-dwf': 'dwf',

  'dwf-to-dwg': 'dwg',

  'dwg-to-dxf': 'dxf',

  'dxf-to-dwg': 'dwg',

  'pdf-to-cad': 'dwg',

  'audio-to-mp3': 'mp3',

  'audio-to-wav': 'wav',

  'audio-to-flac': 'flac',

  'audio-to-m4a': 'm4a',

  'video-to-mp4': 'mp4',

  'video-to-mp3': 'mp3',

  'video-to-gif': 'gif',

  'gif-to-mp4': 'mp4',

  'video-to-webm': 'webm'

};



async function handleConvertFileSelect(files) {

  if (!files || !files.length) return;

  hideError("convert");

  document.getElementById("convert-progress-wrap").style.display = "none";

  document.getElementById("convert-result-card").style.display = "none";



  selectedConvertFiles = Array.from(files);

  selectedConvertFile = selectedConvertFiles[0];



  const ext = getFileExtension(selectedConvertFile.name).toLowerCase();

  

  if (selectedConvertFiles.length > 1) {

    const totalBytes = selectedConvertFiles.reduce((sum, f) => sum + f.size, 0);

    document.getElementById("convert-filename").innerText = `${selectedConvertFiles.length} Files Selected (Batch)`;

    document.getElementById("convert-filesize").innerText = `${formatBytes(totalBytes)} • ${ext.toUpperCase()}`;

  } else {

    document.getElementById("convert-filename").innerText = selectedConvertFile.name;

    document.getElementById("convert-filesize").innerText = `${formatBytes(selectedConvertFile.size)} • ${ext.toUpperCase()}`;

  }



  document.getElementById("convert-file-info").style.display = "flex";

  document.getElementById("convert-dropzone").style.display = "none";

  if (typeof updateCloudEgressMetric === 'function') updateCloudEgressMetric();
  if (typeof detectFileMagicIntent === 'function') detectFileMagicIntent(selectedConvertFile);



  // If PDF, inspect page count

  if (ext === "pdf" && selectedConvertFiles.length === 1) {

    await inspectPdfPages(selectedConvertFile);

  } else {

    document.getElementById("pdf-page-selector-wrap").style.display = "none";

  }



  // If CAD (DWG / DXF), show CAD plot style selector

  const cadWrap = document.getElementById("cad-plot-style-wrap");

  if (cadWrap) {

    if (ext === "dwg" || ext === "dxf") {

      cadWrap.style.display = "block";

    } else {

      cadWrap.style.display = "none";

    }

  }



  // Dynamic AI Smart Suggestion update based on selected file extension

  const aiMsg = document.getElementById("ai-suggestion-msg");

  if (aiMsg) {

    if (ext === "dwg" || ext === "dxf") {

      aiMsg.innerHTML = `<strong>AutoCAD Drawing Detected:</strong> Using exact CTB pen styles and true lineweights for vector plotting to PDF.`;

    } else if (ext === "docx" || ext === "doc" || ext === "pptx" || ext === "xlsx") {

      aiMsg.innerHTML = `<strong>Office Document Detected:</strong> Converting to crisp searchable vector PDF with preserved formatting.`;

    } else if (ext === "pdf") {

      aiMsg.innerHTML = `<strong>PDF Document Detected:</strong> Ready to convert to Word (.docx), extract images, or apply security options.`;

    } else if (["jpg", "jpeg", "png", "webp", "tiff", "heic"].includes(ext)) {

      aiMsg.innerHTML = `<strong>Image File Detected:</strong> Convert format, optimize file size, or compile into a PDF document.`;

    } else if (["mp4", "mov", "avi", "mkv", "mp3", "wav"].includes(ext)) {

      aiMsg.innerHTML = `<strong>Media File Detected:</strong> High-speed transcoding and audio extraction available.`;

    } else {

      aiMsg.innerHTML = `<strong>File Loaded:</strong> Analyzing format to provide the fastest vector and document conversion.`;

    }

  }



  // Update step indicators: Step 1 completed, Step 2 active

  const step1 = document.getElementById('step-node-1');

  const step2 = document.getElementById('step-node-2');

  if (step1) { step1.classList.remove('active'); step1.classList.add('completed'); }

  if (step2) { step2.classList.add('active'); }



  const targetPresetBanner = document.getElementById("convert-target-preset");

  const targetPresetText = document.getElementById("convert-target-preset-text");

  const targetWrap = document.getElementById("convert-target-wrap");

  const btn = document.getElementById("convert-submit-btn");

  const btnText = document.getElementById("convert-btn-text");



  const isDirectPdf = activeQuickTool && DIRECT_PDF_TOOLS.includes(activeQuickTool);

  const isDirectTarget = activeQuickTool && DIRECT_TARGET_MAP[activeQuickTool];

  const isPdfStudioOp = activeQuickTool && [

    'split-pdf', 'rotate-pdf', 'delete-pages', 'protect-pdf', 'unlock-pdf',

    'redact-pdf', 'flatten-pdf', 'repair-pdf', 'extract-images', 'print-ready-pdf'

  ].includes(activeQuickTool);



  if (isDirectPdf) {

    if (targetPresetBanner) targetPresetBanner.style.display = "flex";

    if (targetPresetText) targetPresetText.innerHTML = `Target Format: <strong>PDF Document (.pdf)</strong>`;

    if (targetWrap) targetWrap.style.display = "none";

    btn.disabled = false;

    if (btnText) {

      btnText.innerText = selectedConvertFiles.length > 1

        ? `Convert ${selectedConvertFiles.length} Files to PDF (ZIP)`

        : "Convert to PDF";

    }

  } else if (isDirectTarget) {

    const tgt = DIRECT_TARGET_MAP[activeQuickTool];

    if (targetPresetBanner) targetPresetBanner.style.display = "flex";

    if (targetPresetText) targetPresetText.innerHTML = `Target Format: <strong>${tgt.toUpperCase()} (.${tgt})</strong>`;

    if (targetWrap) targetWrap.style.display = "none";

    btn.disabled = false;

    if (btnText) {

      btnText.innerText = selectedConvertFiles.length > 1

        ? `Convert ${selectedConvertFiles.length} Files to ${tgt.toUpperCase()} (ZIP)`

        : `Convert to ${tgt.toUpperCase()}`;

    }

  } else if (isPdfStudioOp) {

    if (targetPresetBanner) targetPresetBanner.style.display = "none";

    if (targetWrap) targetWrap.style.display = "none";

    btn.disabled = false;

    if (btnText) {

      const toolTitle = activeQuickTool.replace(/-/g, ' ').replace(/pdf/g, 'PDF').toUpperCase();

      btnText.innerText = `Execute ${toolTitle}`;

    }

  } else {

    // Generic / Universal Converter

    if (targetPresetBanner) targetPresetBanner.style.display = "none";

    populateTargetFormats(ext);

    if (targetWrap) targetWrap.style.display = "block";

    btn.disabled = false;

    if (btnText) {

      btnText.innerText = selectedConvertFiles.length > 1

        ? `Convert ${selectedConvertFiles.length} Files (Download ZIP)`

        : "Convert File";

    }

  }



  lucide.createIcons();

}



async function inspectPdfPages(file) {

  try {

    const formData = new FormData();

    formData.append("file", file);

    const res = await fetch("/api/inspect", { method: "POST", body: formData });

    if (res.ok) {

      const data = await res.json();

      inspectedPdfPageCount = data.page_count || 1;

      updatePdfPageSelector(inspectedPdfPageCount);

    }

  } catch (err) {

    console.warn("Inspect failed:", err);

  }

}



function updatePdfPageSelector(pageCount) {

  const wrap = document.getElementById("pdf-page-selector-wrap");

  const select = document.getElementById("pdf-page-select");

  if (!select) return;

  select.innerHTML = "";



  if (pageCount > 1) {

    // Add "All Pages (ZIP)" option

    const optAll = document.createElement("option");

    optAll.value = "all";

    optAll.innerText = `All ${pageCount} Pages (Download as ZIP Archive)`;

    select.appendChild(optAll);



    // Add individual page options

    for (let i = 1; i <= pageCount; i++) {

      const opt = document.createElement("option");

      opt.value = String(i);

      opt.innerText = `Page ${i} of ${pageCount}`;

      select.appendChild(opt);

    }

    wrap.style.display = "block";

  } else {

    wrap.style.display = "none";

  }

}



function clearConvertFile(e) {

  if (e) e.stopPropagation();

  selectedConvertFile = null;

  selectedConvertFiles = [];

  if (typeof updateCloudEgressMetric === 'function') updateCloudEgressMetric();

  document.getElementById("convert-file-info").style.display = "none";

  document.getElementById("convert-dropzone").style.display = "block";
  const intentWrap = document.getElementById("magic-drop-intent-wrap");
  if (intentWrap) intentWrap.style.display = "none";

  document.getElementById("convert-file-input").value = "";

  

  if (!activeQuickTool || !DIRECT_PDF_TOOLS.includes(activeQuickTool)) {

    const preset = document.getElementById("convert-target-preset");

    if (preset) preset.style.display = "none";

    const targetWrap = document.getElementById("convert-target-wrap");

    if (targetWrap) targetWrap.style.display = "none";

  }

  

  document.getElementById("pdf-page-selector-wrap").style.display = "none";

  const cadWrap = document.getElementById("cad-plot-style-wrap");

  if (cadWrap) cadWrap.style.display = "none";

  document.getElementById("convert-submit-btn").disabled = true;

  document.getElementById("convert-result-card").style.display = "none";

  document.getElementById("convert-progress-wrap").style.display = "none";

  hideError("convert");



  const aiMsg = document.getElementById("ai-suggestion-msg");

  if (aiMsg) {

    aiMsg.innerHTML = "Tip: Drop a DWG drawing to batch plot with CTB styles, or drop a document to convert to vector PDF.";

  }

}



function populateTargetFormats(ext) {

  const select = document.getElementById("convert-target-select");

  select.innerHTML = '<option value="">Select target format...</option>';



  const formatData = globalCatalog[ext];

  if (formatData && formatData.targets) {

    formatData.targets.forEach(tgt => {

      const opt = document.createElement("option");

      opt.value = tgt;

      const targetMeta = globalCatalog[tgt];

      const targetName = targetMeta ? targetMeta.name : tgt.toUpperCase();

      opt.innerText = `${tgt.toUpperCase()} — ${targetName}`;

      select.appendChild(opt);

    });



    if (formatData.targets.length > 0) {

      select.value = formatData.targets[0];

      onTargetFormatChange();

    }

  }

}



function onTargetFormatChange() {

  const select = document.getElementById("convert-target-select");

  const target = select.value;

  if (!selectedConvertFile || !target) return;



  const srcExt = getFileExtension(selectedConvertFile.name).toLowerCase();

  const srcData = globalCatalog[srcExt];



  // Show or hide PDF page selector depending on target

  if (srcExt === "pdf") {

    const isImgTarget = ["jpg", "jpeg", "png"].includes(target.toLowerCase());

    const wrap = document.getElementById("pdf-page-selector-wrap");

    if (isImgTarget && inspectedPdfPageCount > 1) {

      wrap.style.display = "block";

    } else {

      wrap.style.display = "none";

    }

  }



  // Update Use Case note

  const noteBox = document.getElementById("convert-use-case-note");

  const noteText = document.getElementById("convert-use-case-text");



  let useCase = "";

  if (srcData && srcData.use_cases && srcData.use_cases[target]) {

    useCase = srcData.use_cases[target];

  } else if (globalCatalog[target]) {

    useCase = globalCatalog[target].description;

  }



  if (useCase) {

    noteText.innerText = `Why convert: ${useCase}`;

    noteBox.style.display = "flex";

  } else {

    noteBox.style.display = "none";

  }

}



async function executeConvert() {

  if (!selectedConvertFiles || !selectedConvertFiles.length) return;

  

  // Check if active tool is a specialized PDF Studio operation

  if (activeQuickTool) {

    const pdfToolMap = {

      'split-pdf': 'split',

      'rotate-pdf': 'rotate',

      'delete-pages': 'delete-pages',

            'sign-pdf': 'sign',
      'sign': 'sign',
      'watermark-pdf': 'watermark',
      'watermark': 'watermark',
      'page-numbers-pdf': 'page-numbers',
      'crop-pdf': 'crop',
      'crop': 'crop',
      'protect-pdf': 'protect',

      'unlock-pdf': 'unlock',

      'redact-pdf': 'redact',

      'flatten-pdf': 'flatten',

      'repair-pdf': 'repair',

      'extract-images': 'extract-images',

      'pdf-to-word': 'to-word',

      'pdf-to-excel': 'to-excel',

      'pdf-to-pptx': 'to-pptx',

      'pdf-to-jpg': 'to-images',

      'pdf-to-png': 'to-images',

      'pdf-to-pdfa': 'pdfa',

      'print-ready-pdf': 'print-ready'

    };



    if (pdfToolMap[activeQuickTool]) {

      return executePdfToolOperation(pdfToolMap[activeQuickTool]);

    }

  }



  let targetFormat = "";

  if (activeQuickTool && DIRECT_PDF_TOOLS.includes(activeQuickTool)) {

    targetFormat = "pdf";

  } else if (activeQuickTool && DIRECT_TARGET_MAP[activeQuickTool]) {

    targetFormat = DIRECT_TARGET_MAP[activeQuickTool];

  } else {

    targetFormat = document.getElementById("convert-target-select")?.value;

  }



  if (!targetFormat) {

    showError("convert", "Please select a target conversion format.");

    return;

  }



  const isBatch = selectedConvertFiles.length > 1;

  const btn = document.getElementById("convert-submit-btn");

  const btnText = document.getElementById("convert-btn-text");

  const progWrap = document.getElementById("convert-progress-wrap");

  const progBar = document.getElementById("convert-progress-bar");

  const progStage = document.getElementById("convert-progress-stage");

  const progPercent = document.getElementById("convert-progress-percent");

  const resultCard = document.getElementById("convert-result-card");



  hideError("convert");

  btn.disabled = true;

  if (btnText) btnText.innerText = isBatch ? `Converting ${selectedConvertFiles.length} Files...` : "Converting...";

  progWrap.style.display = "block";

  resultCard.style.display = "none";

  progBar.style.width = "20%";

  progPercent.innerText = "20%";

  progStage.innerText = isBatch ? `Processing batch of ${selectedConvertFiles.length} files...` : "Processing conversion...";



  startProcessingHud({

    title: `Local File Converter (${targetFormat.toUpperCase()})`,

    subtitle: isBatch ? `Batch converting ${selectedConvertFiles.length} files...` : `Converting file to ${targetFormat.toUpperCase()}...`,

    badgeText: "WASM SIMD CONVERSION CORE"

  });



  let p = 20;

  const timer = setInterval(() => {

    if (p < 85) {

      p += 15;

      progBar.style.width = `${p}%`;

      progPercent.innerText = `${p}%`;

      updateProcessingHud(p, `Compiling vector data & document structures...`);

    }

  }, 180);



  try {

    let res;

    const cadPlotStyle = document.getElementById("convert-cad-plot-style")?.value || "acad.ctb";

    const convertOptions = {

      page_option: document.getElementById("pdf-page-select")?.value || "all",

      plot_style: cadPlotStyle,

      plot_with_styles: true,

      plot_lineweights: true

    };



    if (isBatch) {

      const formData = new FormData();

      selectedConvertFiles.forEach(f => formData.append("files", f));

      formData.append("target_format", targetFormat);

      formData.append("options", JSON.stringify(convertOptions));

      res = await fetch("/api/convert-batch", { method: "POST", body: formData });

    } else {

      const formData = new FormData();

      formData.append("file", selectedConvertFiles[0]);

      formData.append("target_format", targetFormat);

      formData.append("options", JSON.stringify(convertOptions));

      res = await fetch("/api/convert", { method: "POST", body: formData });

    }



    clearInterval(timer);

    progBar.style.width = "100%";

    progPercent.innerText = "100%";



    if (!res.ok) {

      const err = await res.json().catch(() => ({}));

      if (res.status === 429) {

        showQuotaLimitModal(err.detail || "You have reached your daily free conversion limit.");

      }

      throw new Error(err.detail || "Conversion failed");

    }



    const data = await res.json();

    if (data.quota) {

      updateUserQuotaUI(data.quota);

    }

    if (isBatch) {

      document.getElementById("convert-result-metrics").innerText =

        `Batch converted ${data.file_count} of ${data.total_files} files (${formatBytes(data.original_bytes)} ➔ ${formatBytes(data.converted_bytes)}) in ${data.duration_ms}ms`;

    } else {

      document.getElementById("convert-result-metrics").innerText =

        `${formatBytes(data.original_size)} ➔ ${formatBytes(data.converted_size)} (${data.duration_ms}ms)`;

    }



    const savingsBadge = document.getElementById("convert-result-savings");

    if (savingsBadge) {

      if (data.savings_percent > 0) {

        savingsBadge.innerText = `-${data.savings_percent}% Size`;

        savingsBadge.style.display = "inline-block";

      } else {

        savingsBadge.style.display = "none";

      }

    }



    const dlBtn = document.getElementById("convert-download-btn");

    dlBtn.href = data.download_url;

    dlBtn.setAttribute("download", data.output_filename);

    dlBtn.innerText = `Download ${data.output_filename}`;



    // Update step indicators: Step 2 completed, Step 3 active

    const step2 = document.getElementById('step-node-2');

    const step3 = document.getElementById('step-node-3');

    if (step2) { step2.classList.remove('active'); step2.classList.add('completed'); }

    if (step3) { step3.classList.add('active'); }



    // Hide progress wrap immediately so it never lingers

    progWrap.style.display = "none";

    resultCard.style.display = "block";

    stopProcessingHud();

  } catch (err) {

    clearInterval(timer);

    stopProcessingHud();

    progWrap.style.display = "none";

    showError("convert", `Conversion Error: ${err.message}`);

  } finally {

    btn.disabled = false;

    if (btnText) {

      if (activeQuickTool && DIRECT_PDF_TOOLS.includes(activeQuickTool)) {

        btnText.innerText = isBatch ? `Convert ${selectedConvertFiles.length} Files to PDF (ZIP)` : "Convert to PDF";

      } else {

        btnText.innerText = isBatch ? `Convert ${selectedConvertFiles.length} Files (Download ZIP)` : "Convert File";

      }

    }

    lucide.createIcons();

  }

}



// -------------------------------------------------------------

// Document Merger Logic

// -------------------------------------------------------------

let mergeFilesQueue = [];



function handleMergeFilesSelect(files) {

  if (!files || !files.length) return;

  hideError("merge");

  document.getElementById("merge-progress-wrap").style.display = "none";

  document.getElementById("merge-result-card").style.display = "none";



  for (let i = 0; i < files.length; i++) {

    mergeFilesQueue.push(files[i]);

  }

  renderMergeQueue();
  updateCloudEgressMetric();
}

function renderMergeQueue() {

  const queueContainer = document.getElementById("merge-queue-container");

  const list = document.getElementById("merge-file-list");

  const submitBtn = document.getElementById("merge-submit-btn");

  const countLabel = document.getElementById("merge-count-label");



  if (mergeFilesQueue.length === 0) {

    queueContainer.style.display = "none";

    submitBtn.disabled = true;

    return;

  }



  queueContainer.style.display = "block";

  countLabel.innerText = `Files to Merge (${mergeFilesQueue.length})`;

  submitBtn.disabled = mergeFilesQueue.length < 2;



  list.innerHTML = "";

  mergeFilesQueue.forEach((file, index) => {

    const ext = getFileExtension(file.name).toLowerCase();

    const item = document.createElement("div");

    item.className = "cb-queue-item";

    item.innerHTML = `

      <div style="display: flex; align-items: center; gap: 10px; overflow: hidden; flex: 1;">

        <div style="color: var(--cb-blue); flex-shrink: 0;">

          <i data-lucide="${getFileIcon(ext)}" style="width: 18px; height: 18px;"></i>

        </div>

        <div style="overflow: hidden;">

          <div style="font-weight: 700; font-size: 0.88rem; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;" title="${file.name}">

            ${index + 1}. ${file.name}

          </div>

          <div style="font-size: 0.74rem; color: var(--text-secondary);">

            ${formatBytes(file.size)} • ${ext.toUpperCase()}

          </div>

        </div>

      </div>

      <div style="display: flex; align-items: center; gap: 4px; flex-shrink: 0;">

        <button class="cb-icon-btn" title="Move Up" ${index === 0 ? "disabled" : ""} onclick="moveMergeQueueItem(${index}, -1)">

          <i data-lucide="chevron-up" style="width: 16px; height: 16px;"></i>

        </button>

        <button class="cb-icon-btn" title="Move Down" ${index === mergeFilesQueue.length - 1 ? "disabled" : ""} onclick="moveMergeQueueItem(${index}, 1)">

          <i data-lucide="chevron-down" style="width: 16px; height: 16px;"></i>

        </button>

        <button class="cb-icon-btn" title="Remove" onclick="removeMergeQueueItem(${index})" style="color: #EF4444;">

          <i data-lucide="trash-2" style="width: 16px; height: 16px;"></i>

        </button>

      </div>

    `;

    list.appendChild(item);

  });

  lucide.createIcons();

}



function moveMergeQueueItem(index, direction) {

  const newIndex = index + direction;

  if (newIndex < 0 || newIndex >= mergeFilesQueue.length) return;

  const temp = mergeFilesQueue[index];

  mergeFilesQueue[index] = mergeFilesQueue[newIndex];

  mergeFilesQueue[newIndex] = temp;

  renderMergeQueue();

}



function removeMergeQueueItem(index) {

  mergeFilesQueue.splice(index, 1);

  renderMergeQueue();
  updateCloudEgressMetric();

}



function clearMergeQueue() {

  mergeFilesQueue = [];
  updateCloudEgressMetric();

  const fileInput = document.getElementById("merge-file-input");

  if (fileInput) fileInput.value = "";

  document.getElementById("merge-result-card").style.display = "none";

  document.getElementById("merge-progress-wrap").style.display = "none";

  hideError("merge");

  renderMergeQueue();

}



async function executeMerge() {

  if (mergeFilesQueue.length < 2) return;



  const btn = document.getElementById("merge-submit-btn");

  const btnText = document.getElementById("merge-btn-text");

  const progWrap = document.getElementById("merge-progress-wrap");

  const progBar = document.getElementById("merge-progress-bar");

  const resultCard = document.getElementById("merge-result-card");



  hideError("merge");

  btn.disabled = true;

  btnText.innerText = "Merging Files...";

  progWrap.style.display = "block";

  resultCard.style.display = "none";

  progBar.style.width = "25%";



  startProcessingHud({

    title: "Document & PDF Set Merger",

    subtitle: `Combining ${mergeFilesQueue.length} files into unified vector document...`,

    badgeText: "WASM SIMD ASSEMBLY ENGINE"

  });



  const formData = new FormData();

  mergeFilesQueue.forEach(f => {

    formData.append("files", f);

  });



  let p = 25;

  const timer = setInterval(() => {

    if (p < 85) {

      p += 15;

      progBar.style.width = `${p}%`;

      updateProcessingHud(p, "Assembling page structures & merging streams...");

    }

  }, 180);



  try {

    const res = await fetch("/api/merge", { method: "POST", body: formData });

    clearInterval(timer);

    progBar.style.width = "100%";



    if (!res.ok) {

      const err = await res.json();

      throw new Error(err.detail || "Merge failed");

    }



    const data = await res.json();

    document.getElementById("merge-result-metrics").innerText =

      `Merged ${data.file_count} files (${data.pages} pages, ${formatBytes(data.merged_bytes)}) in ${data.duration_ms}ms`;



    const dlBtn = document.getElementById("merge-download-btn");

    dlBtn.href = data.download_url;

    dlBtn.setAttribute("download", data.output_filename);

    dlBtn.innerText = `Download ${data.output_filename}`;



    // Hide progress bar immediately upon showing results

    progWrap.style.display = "none";

    resultCard.style.display = "block";

    stopProcessingHud();

  } catch (err) {

    clearInterval(timer);

    stopProcessingHud();

    progWrap.style.display = "none";

    showError("merge", `Merge Error: ${err.message}`);

  } finally {

    btn.disabled = false;

    btnText.innerText = "Merge Into Single PDF";

    lucide.createIcons();

  }

}



// -------------------------------------------------------------

// Resize Logic

// -------------------------------------------------------------

function handleResizeFileSelect(files) {

  if (!files || !files.length) return;

  hideError("resize");

  document.getElementById("resize-progress-wrap").style.display = "none";

  document.getElementById("resize-result-card").style.display = "none";



  selectedResizeFile = files[0];
  updateCloudEgressMetric();



  const ext = getFileExtension(selectedResizeFile.name).toLowerCase();

  document.getElementById("resize-filename").innerText = selectedResizeFile.name;

  document.getElementById("resize-filesize").innerText = `${formatBytes(selectedResizeFile.size)} • ${ext.toUpperCase()}`;

  document.getElementById("resize-file-info").style.display = "flex";

  document.getElementById("resize-dropzone").style.display = "none";

  document.getElementById("resize-submit-btn").disabled = false;



  if (ext === "pdf") switchResizeSubTab("pdf");

  else if (["png", "jpg", "jpeg", "webp"].includes(ext)) switchResizeSubTab("image");

  else if (["mp4", "mkv", "mov", "avi"].includes(ext)) switchResizeSubTab("video");

  lucide.createIcons();

}



function clearResizeFile(e) {

  if (e) e.stopPropagation();

  selectedResizeFile = null;
  updateCloudEgressMetric();

  document.getElementById("resize-file-info").style.display = "none";

  document.getElementById("resize-dropzone").style.display = "block";

  document.getElementById("resize-file-input").value = "";

  document.getElementById("resize-submit-btn").disabled = true;

  document.getElementById("resize-result-card").style.display = "none";

  document.getElementById("resize-progress-wrap").style.display = "none";

  hideError("resize");

}



async function executeResize() {

  if (!selectedResizeFile) return;



  const btn = document.getElementById("resize-submit-btn");

  const btnText = document.getElementById("resize-btn-text");

  const progWrap = document.getElementById("resize-progress-wrap");

  const progBar = document.getElementById("resize-progress-bar");

  const resultCard = document.getElementById("resize-result-card");



  hideError("resize");

  btn.disabled = true;

  btnText.innerText = "Optimizing...";

  progWrap.style.display = "block";

  resultCard.style.display = "none";

  progBar.style.width = "25%";



  const formData = new FormData();

  formData.append("file", selectedResizeFile);

  formData.append("tool_type", activeResizeType);



  const opts = {};

  if (activeResizeType === "pdf") {

    opts.target_size = document.getElementById("pdf-page-size")?.value || document.getElementById("pdf-target-size")?.value || "keep";

    const targetVal = document.getElementById("pdf-target-kb")?.value || document.getElementById("pdf-target-size-val")?.value;

    const targetUnit = document.getElementById("pdf-size-unit")?.value || document.getElementById("pdf-target-size-unit")?.value || "kb";

    if (targetVal && parseFloat(targetVal) > 0) {

      opts.target_size_val = parseFloat(targetVal);

      opts.target_size_unit = targetUnit;

    }

  } else if (activeResizeType === "image") {

    const w = parseInt(document.getElementById("img-width")?.value);

    const h = parseInt(document.getElementById("img-height")?.value);

    const q = parseInt(document.getElementById("img-quality")?.value);

    if (!isNaN(w)) opts.width = w;

    if (!isNaN(h)) opts.height = h;

    opts.quality = !isNaN(q) ? q : 85;

  } else if (activeResizeType === "video") {

    opts.resolution = document.getElementById("video-resolution").value;

  }

  formData.append("options", JSON.stringify(opts));



  let p = 25;

  const timer = setInterval(() => {

    if (p < 85) { p += 15; progBar.style.width = `${p}%`; }

  }, 180);



  try {

    const res = await fetch("/api/resize", { method: "POST", body: formData });

    clearInterval(timer);

    progBar.style.width = "100%";



    if (!res.ok) {

      const err = await res.json();

      throw new Error(err.detail || "Resize failed");

    }



    const data = await res.json();

    const stats = data.stats || {};

    document.getElementById("resize-result-metrics").innerText =

      `${formatBytes(stats.original_bytes)} ➔ ${formatBytes(stats.new_bytes)} (${data.duration_ms}ms)`;



    const savingsBadge = document.getElementById("resize-result-savings");

    if (stats.savings_percent > 0) {

      savingsBadge.innerText = `-${stats.savings_percent}% Size`;

      savingsBadge.style.display = "inline-block";

    } else {

      savingsBadge.style.display = "none";

    }



    const dlBtn = document.getElementById("resize-download-btn");

    dlBtn.href = data.download_url;

    dlBtn.setAttribute("download", data.output_filename);

    dlBtn.innerText = `Download ${data.output_filename}`;



    // Hide progress bar immediately when showing results

    progWrap.style.display = "none";

    resultCard.style.display = "block";

  } catch (err) {

    clearInterval(timer);

    progWrap.style.display = "none";

    showError("resize", `Resize failed: ${err.message}`);

  } finally {

    btn.disabled = false;

    btnText.innerText = "Resize & Compress";

    lucide.createIcons();

  }

}



// -------------------------------------------------------------

// Helpers

// -------------------------------------------------------------



function getFileExtension(name) {

  return name.slice((name.lastIndexOf(".") - 1 >>> 0) + 2);

}



function formatBytes(bytes, decimals = 1) {

  if (!bytes) return '0 B';

  const k = 1024;

  const dm = decimals < 0 ? 0 : decimals;

  const sizes = ['B', 'KB', 'MB', 'GB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];

}

// =============================================================
// LIVE UPLOADED AMOUNT & PROCESSED METRIC TRACKER
// =============================================================
let sessionUploadedBytes = parseInt(sessionStorage.getItem("ilf_session_bytes") || "0", 10);
let sessionProcessedCount = parseInt(sessionStorage.getItem("ilf_session_files") || "0", 10);

function updateCloudEgressMetric(addedBytes = 0, addedFiles = 0) {
  if (addedBytes > 0) {
    sessionUploadedBytes += addedBytes;
    sessionStorage.setItem("ilf_session_bytes", sessionUploadedBytes);
  }
  if (addedFiles > 0) {
    sessionProcessedCount += addedFiles;
    sessionStorage.setItem("ilf_session_files", sessionProcessedCount);
  }

  let stagedBytes = 0;
  let stagedCount = 0;

  if (typeof landingStudioFiles !== "undefined" && Array.isArray(landingStudioFiles)) {
    stagedBytes += landingStudioFiles.reduce((sum, f) => sum + (f.size || 0), 0);
    stagedCount += landingStudioFiles.length;
  }
  if (typeof selectedPlotFiles !== "undefined" && Array.isArray(selectedPlotFiles)) {
    stagedBytes += selectedPlotFiles.reduce((sum, f) => sum + (f.size || 0), 0);
    stagedCount += selectedPlotFiles.length;
  }
  if (typeof selectedPcmlFiles !== "undefined" && Array.isArray(selectedPcmlFiles)) {
    stagedBytes += selectedPcmlFiles.reduce((sum, f) => sum + (f.size || 0), 0);
    stagedCount += selectedPcmlFiles.length;
  }
  if (typeof selectedConvertFiles !== "undefined" && Array.isArray(selectedConvertFiles)) {
    stagedBytes += selectedConvertFiles.reduce((sum, f) => sum + (f.size || 0), 0);
    stagedCount += selectedConvertFiles.length;
  }
  if (typeof mergeFilesQueue !== "undefined" && Array.isArray(mergeFilesQueue)) {
    stagedBytes += mergeFilesQueue.reduce((sum, f) => sum + (f.size || 0), 0);
    stagedCount += mergeFilesQueue.length;
  }
  if (typeof selectedResizeFile !== "undefined" && selectedResizeFile && selectedResizeFile.size) {
    stagedBytes += selectedResizeFile.size;
    stagedCount += 1;
  }

  const valEl = document.getElementById("metric-cloud-egress-val");
  const subEl = document.getElementById("metric-cloud-egress-sub");

  const totalEffectiveBytes = stagedBytes > 0 ? stagedBytes : sessionUploadedBytes;
  const totalEffectiveFiles = stagedCount > 0 ? stagedCount : sessionProcessedCount;

  if (valEl) {
    if (totalEffectiveBytes > 0) {
      valEl.innerText = formatBytes(totalEffectiveBytes);
      valEl.classList.remove("text-emerald-bright");
      valEl.style.color = "var(--terracotta, #ea580c)";
    } else {
      valEl.innerText = "0.00 KB";
      valEl.style.color = "";
      valEl.classList.add("text-emerald-bright");
    }
  }

  if (subEl) {
    if (stagedCount > 0) {
      subEl.innerText = `${stagedCount} file${stagedCount > 1 ? "s" : ""} staged • 100% private local`;
    } else if (sessionUploadedBytes > 0) {
      subEl.innerText = `${sessionProcessedCount} file${sessionProcessedCount > 1 ? "s" : ""} processed • Zero cloud egress`;
    } else {
      subEl.innerText = "Zero data uploaded";
    }
  }
}




function getFileIcon(ext) {

  if (ext === "pdf") return "file-text";

  if (["png", "jpg", "jpeg", "webp", "gif", "tiff", "bmp"].includes(ext)) return "image";

  if (["docx", "doc", "txt", "md"].includes(ext)) return "file-text";

  if (["mp4", "mkv", "mov", "avi"].includes(ext)) return "video";

  if (["mp3", "wav", "flac"].includes(ext)) return "music";

  return "file";

}



// -------------------------------------------------------------

// AutoCAD Batch Plot & Publish Studio

// -------------------------------------------------------------

function handlePlotFilesSelect(files) {

  if (!files || files.length === 0) return;

  const errBanner = document.getElementById("plot-error-banner");

  if (errBanner) errBanner.style.display = "none";

  const progWrap = document.getElementById("plot-progress-wrap");

  if (progWrap) progWrap.style.display = "none";

  const resCard = document.getElementById("plot-result-card");

  if (resCard) resCard.style.display = "none";



  for (let i = 0; i < files.length; i++) {

    const f = files[i];

    const ext = getFileExtension(f.name).toLowerCase();

    if (ext === "dwg" || ext === "dxf") {

      selectedPlotFiles.push(f);

    }

  }

  renderPlotQueue();
  updateCloudEgressMetric();
  lucide.createIcons();
}



function renderPlotQueue() {

  const container = document.getElementById("plot-queue-container");

  const list = document.getElementById("plot-queue-list");

  const countLabel = document.getElementById("plot-queue-count-label");

  const submitBtn = document.getElementById("plot-submit-btn");



  if (!container || !list) return;



  if (selectedPlotFiles.length === 0) {

    container.style.display = "none";

    if (submitBtn) submitBtn.disabled = true;

    return;

  }



  container.style.display = "block";

  if (countLabel) countLabel.innerText = `Batch Drawing Queue (${selectedPlotFiles.length} Drawing${selectedPlotFiles.length > 1 ? 's' : ''})`;

  if (submitBtn) submitBtn.disabled = false;



  list.innerHTML = selectedPlotFiles.map((file, idx) => `

    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.85rem; border: 1px solid var(--border-ink); background: var(--bg-bone-subtle); box-shadow: 1px 1px 0px rgba(0,0,0,0.5);">

      <div style="display: flex; align-items: center; gap: 0.6rem; overflow: hidden;">

        <i data-lucide="layers" style="width: 14px; height: 14px; color: var(--accent-ember); flex-shrink: 0;"></i>

        <span style="font-size: 0.82rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${file.name}</span>

        <span style="font-size: 0.72rem; color: var(--text-muted);">(${formatBytes(file.size)})</span>

      </div>

      <button type="button" class="file-loaded-remove" style="width: 24px; height: 24px;" onclick="removePlotFile(${idx})" title="Remove drawing">

        <i data-lucide="x" style="width: 12px; height: 12px;"></i>

      </button>

    </div>

  `).join("");



  lucide.createIcons();

}



function removePlotFile(idx) {

  selectedPlotFiles.splice(idx, 1);

  renderPlotQueue();
  updateCloudEgressMetric();

}



function handleCtbFileSelect(files) {

  if (!files || files.length === 0) return;

  selectedCustomCtb = files[0];

  const badge = document.getElementById("plot-ctb-loaded-badge");

  const filenameSpan = document.getElementById("plot-ctb-filename");

  if (badge && filenameSpan) {

    filenameSpan.innerText = selectedCustomCtb.name;

    badge.style.display = "block";

  }

  lucide.createIcons();

}



function clearCustomCtb() {

  selectedCustomCtb = null;

  const badge = document.getElementById("plot-ctb-loaded-badge");

  const input = document.getElementById("plot-ctb-file");

  if (badge) badge.style.display = "none";

  if (input) input.value = "";

}



async function submitAutoCadBatchPlot() {

  if (selectedPlotFiles.length === 0) return;



  const btn = document.getElementById("plot-submit-btn");

  const btnText = document.getElementById("plot-submit-btn-text");

  const progWrap = document.getElementById("plot-progress-wrap");

  const progFill = document.getElementById("plot-progress-fill");

  const progStatus = document.getElementById("plot-prog-status");

  const progPercent = document.getElementById("plot-prog-percent");

  const resultCard = document.getElementById("plot-result-card");

  const errBanner = document.getElementById("plot-error-banner");



  if (errBanner) errBanner.style.display = "none";

  if (resultCard) resultCard.style.display = "none";

  btn.disabled = true;

  btnText.innerText = "Executing AutoCAD Batch Plot...";

  progWrap.style.display = "block";

  progFill.style.width = "10%";

  progPercent.innerText = "10%";

  progStatus.innerText = "Initializing Autodesk AutoCAD 2026 Core Console...";



  let pct = 8;

  const numFiles = selectedPlotFiles.length;

  // Estimate ~12 seconds per drawing with minimum 20s

  const estTotalSec = Math.max(20, numFiles * 12);

  const stepMs = Math.round((estTotalSec * 1000) / 85);



  const currentPlotStyle = selectedCustomCtb ? selectedCustomCtb.name : (document.getElementById("plot-style")?.value || "acad.ctb");

  startProcessingHud({

    title: "AutoCAD Batch Plotting Studio",

    subtitle: `Staging ${numFiles} drawing(s) & applying ${currentPlotStyle}...`,

    badgeText: "AUTOCAD 2026 CORE REFINERY"

  });



  const timer = setInterval(() => {

    if (pct < 94) {

      pct += 1;

      progFill.style.width = `${pct}%`;

      progPercent.innerText = `${pct}%`;

      if (pct === 15) progStatus.innerText = "Staging DWG models & applying CTB pen table...";

      if (pct === 35) progStatus.innerText = `AutoCAD 2026 Core Console vector plotting in progress (${numFiles} file${numFiles > 1 ? 's' : ''})...`;

      if (pct === 60) progStatus.innerText = "Extracting crisp vector lineweights & layers...";

      if (pct === 80) progStatus.innerText = "Assembling multi-sheet drawing set & booklet...";

      if (pct === 90) progStatus.innerText = "Finalizing high-resolution output...";

      updateProcessingHud(pct, progStatus.innerText);

    }

  }, stepMs);



  const fd = new FormData();

  selectedPlotFiles.forEach(f => fd.append("files", f));

  if (selectedCustomCtb) {

    fd.append("ctb_file", selectedCustomCtb);

  }



  const printer = document.getElementById("plot-printer").value;

  const paperSize = document.getElementById("plot-paper-size").value;

  const plotStyle = document.getElementById("plot-style").value;

  const plotArea = document.getElementById("plot-area").value;

  const centerPlot = document.getElementById("plot-center").checked;

  const fitPaper = document.getElementById("plot-fit").checked;

  const orientation = document.querySelector('input[name="plot_orientation"]:checked')?.value || "Landscape";

  const plotLineweights = document.getElementById("plot-lineweights").checked;

  const plotWithStyles = document.getElementById("plot-styles-enabled").checked;

  const shadePlot = document.getElementById("plot-shade").value;

  const isUnified = document.getElementById("plot-pack-unified").checked;



  fd.append("printer", printer);

  fd.append("paper_size", paperSize);

  fd.append("plot_style", plotStyle);

  fd.append("plot_area", plotArea);

  fd.append("center_plot", centerPlot);

  fd.append("fit_to_paper", fitPaper);

  fd.append("orientation", orientation);

  fd.append("plot_lineweights", plotLineweights);

  fd.append("plot_with_styles", plotWithStyles);

  fd.append("shade_plot", shadePlot);

  fd.append("merge_output", isUnified);



  const controller = new AbortController();

  const timeoutId = setTimeout(() => controller.abort(), 180000); // 3-minute safety timeout



  try {

    const res = await fetch("/api/cad/batch-plot", {

      method: "POST",

      body: fd,

      signal: controller.signal

    });

    clearTimeout(timeoutId);



    clearInterval(timer);



    if (!res.ok) {

      const err = await res.json().catch(() => ({}));

      if (res.status === 429 || res.status === 403) {

        showQuotaLimitModal(err.detail || "AutoCAD batch plotting requires a Pro subscription.");

      }

      throw new Error(err.detail || "Batch plot failed.");

    }



    const data = await res.json();

    if (data.quota) {

      updateUserQuotaUI(data.quota);

    }

    progFill.style.width = "100%";

    progPercent.innerText = "100%";

    progStatus.innerText = "Batch plot complete!";



    const sheetsEl = document.getElementById("plot-res-sheets");

    if (sheetsEl) sheetsEl.innerText = data.sheets_plotted;

    const sizeEl = document.getElementById("plot-res-size");

    if (sizeEl) sizeEl.innerText = formatBytes(data.file_size);

    const ctbEl = document.getElementById("plot-res-ctb");

    if (ctbEl) ctbEl.innerText = data.plot_style;

    const durEl = document.getElementById("plot-res-duration");

    if (durEl) durEl.innerText = `${(data.duration_ms / 1000).toFixed(1)}s`;



    const dlBtn = document.getElementById("plot-download-btn");

    if (dlBtn) {

      dlBtn.href = data.download_url;

      dlBtn.setAttribute("download", data.output_filename);

      dlBtn.innerText = `Download ${data.output_filename}`;

    }



    const previewContainer = document.getElementById("plot-preview-container");

    const previewImg = document.getElementById("plot-preview-img");

    const previewSource = data.preview_data_url || data.preview_url;

    if (previewSource && previewContainer && previewImg) {

      previewImg.src = previewSource;

      previewContainer.style.display = "block";

    } else if (previewContainer) {

      previewContainer.style.display = "none";

    }



    if (progWrap) progWrap.style.display = "none";

    if (resultCard) resultCard.style.display = "block";

    stopProcessingHud();

  } catch (err) {

    clearInterval(timer);

    stopProcessingHud();

    progWrap.style.display = "none";

    if (errBanner) {

      document.getElementById("plot-error-text").innerText = `Plotting failed: ${err.message}`;

      errBanner.style.display = "flex";

    }

  } finally {

    btn.disabled = false;

    btnText.innerText = "Execute AutoCAD Batch Plot";

    lucide.createIcons();

  }

}



function resetPlotStudio() {

  selectedPlotFiles = [];

  renderPlotQueue();

  const resCard = document.getElementById("plot-result-card");

  if (resCard) resCard.style.display = "none";

  const errBanner = document.getElementById("plot-error-banner");

  if (errBanner) errBanner.style.display = "none";

}







// =============================================================

// ZAPIER SETTINGS & OFF+BRAND 324+ CONVERTER & PDF STUDIO

// =============================================================

let activeQuickTool = null;

let activeRotateAngle = 90;



function selectQuickTool(toolId, title, acceptedExt) {

  hideError("convert");

  activeQuickTool = toolId;

  

  // Highlight active card

  document.querySelectorAll('.tool-card').forEach(c => c.classList.remove('active'));

  const card = document.getElementById(`card-${toolId}`);

  if (card) card.classList.add('active');



  // Update step indicators

  const step1 = document.getElementById('step-node-1');

  const step2 = document.getElementById('step-node-2');

  if (step1) { step1.classList.remove('active'); step1.classList.add('completed'); }

  if (step2) { step2.classList.add('active'); }



  // Open contextual drawer

  const drawer = document.getElementById('context-config-drawer');

  if (drawer) {

    drawer.style.display = 'block';

    const titleElem = document.getElementById('drawer-tool-title');

    if (titleElem) titleElem.innerText = title.toUpperCase();



    const badgeElem = document.getElementById('drawer-tool-badge');

    if (badgeElem) badgeElem.innerText = "Step 2: Settings";



    const descElem = document.getElementById('drawer-tool-desc');

    if (descElem) descElem.innerText = `Drop your files below to convert with ${title}.`;



    const btnText = document.getElementById('convert-btn-text');

    

    // Set file input accept filter

    const fileInput = document.getElementById('convert-file-input');

    if (fileInput) fileInput.setAttribute('accept', acceptedExt || '*');



    // Hide all option panels first

    document.querySelectorAll('.tool-opt-panel').forEach(p => p.style.display = 'none');

    

    const targetWrap = document.getElementById('convert-target-wrap');

    const targetPreset = document.getElementById('convert-target-preset');

    const targetPresetText = document.getElementById('convert-target-preset-text');



    if (DIRECT_PDF_TOOLS.includes(toolId)) {

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) {

        targetPreset.style.display = 'flex';

        if (targetPresetText) targetPresetText.innerHTML = 'Target Format: <strong>PDF Document (.pdf)</strong>';

      }

      if (btnText) btnText.innerText = 'Convert to PDF';

    } else if (DIRECT_TARGET_MAP[toolId]) {

      const tgt = DIRECT_TARGET_MAP[toolId];

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) {

        targetPreset.style.display = 'flex';

        if (targetPresetText) targetPresetText.innerHTML = `Target Format Preset: <strong>${tgt.toUpperCase()} (.${tgt})</strong>`;

      }

      if (btnText) btnText.innerText = `Convert to ${tgt.toUpperCase()}`;

    } else if (toolId === 'split-pdf') {

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) targetPreset.style.display = 'none';

      const p = document.getElementById('opt-split-pdf');

      if (p) p.style.display = 'block';

      if (btnText) btnText.innerText = 'Split PDF';

    } else if (toolId === 'rotate-pdf') {

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) targetPreset.style.display = 'none';

      const p = document.getElementById('opt-rotate-pdf');

      if (p) p.style.display = 'block';

      if (btnText) btnText.innerText = 'Rotate PDF';

    } else if (toolId === 'delete-pages') {

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) targetPreset.style.display = 'none';

      const p = document.getElementById('opt-delete-pages');

      if (p) p.style.display = 'block';

      if (btnText) btnText.innerText = 'Delete Selected Pages';

        } else if (toolId === 'sign-pdf' || toolId === 'sign') {
      if (targetWrap) targetWrap.style.display = 'none';
      if (targetPreset) targetPreset.style.display = 'none';
      const p = document.getElementById('opt-sign-pdf');
      if (p) p.style.display = 'block';
      if (btnText) btnText.innerText = 'Sign & Seal PDF';
    } else if (toolId === 'watermark-pdf' || toolId === 'watermark') {
      if (targetWrap) targetWrap.style.display = 'none';
      if (targetPreset) targetPreset.style.display = 'none';
      const p = document.getElementById('opt-watermark-pdf');
      if (p) p.style.display = 'block';
      if (btnText) btnText.innerText = 'Apply Watermark';
    } else if (toolId === 'page-numbers-pdf' || toolId === 'page-numbers') {
      if (targetWrap) targetWrap.style.display = 'none';
      if (targetPreset) targetPreset.style.display = 'none';
      const p = document.getElementById('opt-page-numbers-pdf');
      if (p) p.style.display = 'block';
      if (btnText) btnText.innerText = 'Add Page Numbers';
    } else if (toolId === 'crop-pdf' || toolId === 'crop') {
      if (targetWrap) targetWrap.style.display = 'none';
      if (targetPreset) targetPreset.style.display = 'none';
      const p = document.getElementById('opt-crop-pdf');
      if (p) p.style.display = 'block';
      if (btnText) btnText.innerText = 'Crop PDF Margins';
    } else if (toolId === 'protect-pdf') {

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) targetPreset.style.display = 'none';

      const p = document.getElementById('opt-protect-pdf');

      if (p) p.style.display = 'block';

      if (btnText) btnText.innerText = 'Protect PDF';

    } else if (toolId === 'unlock-pdf') {

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) targetPreset.style.display = 'none';

      const p = document.getElementById('opt-unlock-pdf');

      if (p) p.style.display = 'block';

      if (btnText) btnText.innerText = 'Unlock PDF';

    } else if (toolId === 'redact-pdf') {

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) targetPreset.style.display = 'none';

      const p = document.getElementById('opt-redact-pdf');

      if (p) p.style.display = 'block';

      if (btnText) btnText.innerText = 'Redact & Purge Keywords';

    } else if (toolId === 'print-ready-pdf') {

      if (targetWrap) targetWrap.style.display = 'none';

      if (targetPreset) targetPreset.style.display = 'none';

      const p = document.getElementById('opt-print-ready-pdf');

      if (p) p.style.display = 'block';

      if (btnText) btnText.innerText = 'Generate Print-Ready PDF';

    } else {

      if (targetPreset) targetPreset.style.display = 'none';

      if (targetWrap) targetWrap.style.display = 'block';

      if (btnText) btnText.innerText = 'Convert File';

    }



    drawer.scrollIntoView({ behavior: 'smooth', block: 'start' });

  }



  // Update button state if file already selected

  const btn = document.getElementById('convert-submit-btn');

  if (btn && selectedConvertFiles && selectedConvertFiles.length > 0) {

    btn.disabled = false;

  }

  lucide.createIcons();

}



function setRotateAngle(angle, btn) {

  activeRotateAngle = angle;

  document.querySelectorAll('.opt-angle-btn').forEach(b => b.classList.remove('active'));

  if (btn) btn.classList.add('active');

}



function toggleSplitMode() {

  const mode = document.querySelector('input[name="split_mode"]:checked')?.value;

  const input = document.getElementById('split-range-input');

  if (input) {

    input.style.display = (mode === 'burst') ? 'none' : 'block';

  }

}



function filterToolCards(query) {

  const q = (query || '').toLowerCase().trim();

  if (q.includes('@') || q.endsWith('.com')) {

    const searchInput = document.getElementById('hub-search-input');

    if (searchInput) searchInput.value = '';

    document.querySelectorAll('.tool-card').forEach(card => {

      card.style.display = 'flex';

    });

    return;

  }

  document.querySelectorAll('.tool-card').forEach(card => {

    const title = (card.querySelector('.tool-label')?.innerText || '').toLowerCase();

    const cat = (card.getAttribute('data-category') || '').toLowerCase();

    const ext = (card.getAttribute('data-ext') || '').toLowerCase();

    const matches = !q || title.includes(q) || cat.includes(q) || ext.includes(q);

    card.style.display = matches ? 'flex' : 'none';

  });

}



function filterCategory(cat) {

  document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));

  const pill = document.getElementById(`pill-${cat}`);

  if (pill) pill.classList.add('active');



  document.querySelectorAll('.tool-card').forEach(card => {

    const cardCat = card.getAttribute('data-category');

    if (cat === 'all' || cardCat === cat) {

      card.style.display = 'flex';

    } else {

      card.style.display = 'none';

    }

  });

}



function toggleFaq(elem) {

  const item = elem.closest('.faq-item');

  if (item) {

    item.classList.toggle('open');

    item.classList.toggle('active');

    lucide.createIcons();

  }

}





async function executePdfToolOperation(operation) {

  const file = selectedConvertFiles[0];

  if (!file) return;



  const btn = document.getElementById("convert-submit-btn");

  const btnText = document.getElementById("convert-btn-text");

  const progWrap = document.getElementById("convert-progress-wrap");

  const progBar = document.getElementById("convert-progress-bar");

  const progStage = document.getElementById("convert-progress-stage");

  const progPercent = document.getElementById("convert-progress-percent");

  const resultCard = document.getElementById("convert-result-card");



  hideError("convert");

  btn.disabled = true;

  if (btnText) btnText.innerText = "Executing...";

  progWrap.style.display = "block";

  resultCard.style.display = "none";

  progBar.style.width = "25%";

  progPercent.innerText = "25%";

  progStage.innerText = `Executing ${operation} locally via PyMuPDF...`;



  startProcessingHud({

    title: `PDF Studio (${operation.toUpperCase()})`,

    subtitle: `Executing ${operation} locally with PyMuPDF...`,

    badgeText: "PYMUPDF LOCAL ENGINE"

  });



  let p = 25;

  const timer = setInterval(() => {

    if (p < 85) {

      p += 15;

      progBar.style.width = `${p}%`;

      progPercent.innerText = `${p}%`;

      updateProcessingHud(p, `Executing ${operation} with zero cloud egress...`);

    }

  }, 150);



  const fd = new FormData();

  fd.append("file", file);



  const opts = {};

  if (operation === "split") {

    const mode = document.querySelector('input[name="split_mode"]:checked')?.value;

    opts.burst = (mode === "burst");

    opts.ranges = document.getElementById("split-range-input")?.value || "1";

  } else if (operation === "rotate") {

    opts.angle = activeRotateAngle || 90;

  } else if (operation === "delete-pages") {

    opts.pages = document.getElementById("delete-pages-input")?.value || "";

    } else if (operation === "sign") {
    opts.signer = document.getElementById("sign-name-input")?.value || "Musthaque Ali";
    opts.initials = document.getElementById("sign-initials-input")?.value || "MA";
    opts.reason = document.getElementById("sign-reason-input")?.value || "Approved & Verified";
    opts.page = parseInt(document.getElementById("sign-page-input")?.value || "1", 10);
    opts.sig_type = activeSignType || "simple";
    opts.position = document.getElementById("sign-placement-pos")?.value || "bottom-right";
  } else if (operation === "watermark") {
    opts.text = document.getElementById("pdf-watermark-text-input")?.value || "CONFIDENTIAL";
    opts.opacity = parseFloat(document.getElementById("pdf-watermark-opacity")?.value || "0.25");
    opts.angle = parseFloat(document.getElementById("pdf-watermark-angle")?.value || "45.0");
  } else if (operation === "page-numbers") {
    opts.position = document.getElementById("pdf-page-numbers-pos")?.value || "bottom-center";
    opts.format = document.getElementById("pdf-page-numbers-fmt")?.value || "Page {page} of {total}";
  } else if (operation === "crop") {
    opts.margin = parseFloat(document.getElementById("pdf-crop-margin")?.value || "0.05");
  } else if (operation === "protect") {

    const pwd = document.getElementById("protect-password-input")?.value || "";

    if (!pwd) {

      showError("convert", "Please enter a password to protect this PDF.");

      btn.disabled = false;

      progWrap.style.display = "none";

      stopProcessingHud();

      if (btnText) btnText.innerText = "Protect PDF";

      return;

    }

    opts.password = pwd;

  } else if (operation === "unlock") {

    opts.password = document.getElementById("unlock-password-input")?.value || "";

  } else if (operation === "redact") {

    opts.keywords = document.getElementById("redact-keywords-input")?.value || "";

  } else if (operation === "to-images") {

    opts.format = activeQuickTool === "pdf-to-jpg" ? "jpg" : "png";

  } else if (operation === "print-ready") {

    opts.dpi = parseInt(document.getElementById("print-dpi-select")?.value || "300");

  }



  fd.append("options", JSON.stringify(opts));



  try {

    const res = await fetch(`/api/pdf/${operation}`, {

      method: "POST",

      body: fd

    });

    clearInterval(timer);

    progBar.style.width = "100%";

    progPercent.innerText = "100%";



    if (!res.ok) {

      const err = await res.json().catch(() => ({}));

      if (res.status === 429) {

        showQuotaLimitModal(err.detail || "You have reached your daily free conversion limit.");

      }

      throw new Error(err.detail || "Operation failed");

    }



    const data = await res.json();

    if (data.quota) {

      updateUserQuotaUI(data.quota);

    }

    document.getElementById("convert-result-metrics").innerText =

      `${data.output_filename} (${formatBytes(data.file_size)}) generated in ${data.duration_ms}ms`;



    const dlBtn = document.getElementById("convert-download-btn");

    dlBtn.href = data.download_url;

    dlBtn.setAttribute("download", data.output_filename);

    dlBtn.innerText = `Download ${data.output_filename}`;



    // Update step strip to Step 3

    const step2 = document.getElementById('step-node-2');

    const step3 = document.getElementById('step-node-3');

    if (step2) { step2.classList.remove('active'); step2.classList.add('completed'); }

    if (step3) { step3.classList.add('active'); }



    progWrap.style.display = "none";

    resultCard.style.display = "block";

    stopProcessingHud();

  } catch (err) {

    clearInterval(timer);

    stopProcessingHud();

    progWrap.style.display = "none";

    showError("convert", `Error: ${err.message}`);

  } finally {

    btn.disabled = false;

    if (btnText) btnText.innerText = "Execute Operation";

    lucide.createIcons();

  }

}



// ==========================================================================

// THEME MANAGEMENT (LIGHT & DARK THEME)

// ==========================================================================

function getSystemTheme() {

  return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';

}



function getCurrentTheme() {

  return document.documentElement.getAttribute('data-theme') || localStorage.getItem('ilovefiles_theme') || getSystemTheme();

}



function applyTheme(theme, animate = false) {

  if (animate) {

    document.documentElement.classList.add('theme-transitioning');

    window.setTimeout(() => {

      document.documentElement.classList.remove('theme-transitioning');

    }, 300);

  }

  document.documentElement.setAttribute('data-theme', theme);

  try {

    localStorage.setItem('ilovefiles_theme', theme);

  } catch (e) {}



  const btnText = document.getElementById('theme-btn-text');

  const btn = document.getElementById('theme-toggle-btn');

  if (btnText) {

    btnText.innerText = (theme === 'dark') ? 'Light' : 'Dark';

  }

  if (btn) {

    btn.setAttribute('aria-label', `Switch to ${(theme === 'dark') ? 'Light' : 'Dark'} Mode`);

    btn.setAttribute('title', `Switch to ${(theme === 'dark') ? 'Light' : 'Dark'} Mode`);

  }

  if (window.lucide) {

    lucide.createIcons();

  }

}



function toggleTheme() {

  const current = getCurrentTheme();

  const next = (current === 'dark') ? 'light' : 'dark';

  applyTheme(next, true);

}



function initTheme() {

  try {

    const saved = localStorage.getItem('ilovefiles_theme');

    const theme = saved || getSystemTheme();

    applyTheme(theme, false);



    if (window.matchMedia) {

      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {

        if (!localStorage.getItem('ilovefiles_theme')) {

          applyTheme(e.matches ? 'dark' : 'light', true);

        }

      });

    }

  } catch (e) {

    applyTheme('light', false);

  }

}



// ==========================================================================

// SAAS AUTHENTICATION, SUBSCRIPTIONS & QUOTA LOGIC

// ==========================================================================

let currentUser = null;

let billingAnnual = false;

let googleAuthInitialized = false;

let googleClientId = "357128299790-1cqd2nr1lj4859t3q5mf8ok6c3bmonm8.apps.googleusercontent.com";



async function fetchWithTimeout(url, options = {}, timeoutMs = 12000) {

  if (window.location.protocol === 'file:') {

    throw new Error("You opened index.html directly from disk (file://). Please start the backend server with run_app.bat and open http://localhost:8000 in your browser.");

  }

  const controller = new AbortController();

  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {

    const res = await fetch(url, { ...options, signal: controller.signal });

    return res;

  } catch (err) {

    if (err.name === 'AbortError') {

      throw new Error(`Server request timed out (${Math.round(timeoutMs / 1000)}s). Please ensure the backend server is running.`);

    }

    if (err.message && (err.message.includes("Failed to fetch") || err.message.includes("NetworkError"))) {

      throw new Error(`Cannot connect to server at ${window.location.origin}. Please ensure the backend server is running.`);

    }

    throw err;

  } finally {

    clearTimeout(timer);

  }

}



async function initAuth() {

  try {

    // Check if returning from a Cashfree checkout redirect

    const urlParams = new URLSearchParams(window.location.search);

    const returnOrderId = urlParams.get("order_id");

    if (returnOrderId) {

      await verifyCashfreePayment(returnOrderId);

      window.history.replaceState({}, document.title, window.location.pathname);

    }



    // Initialize Google One-Click Auth SDK

    initGoogleAuth();



    const res = await fetchWithTimeout("/api/auth/me", {}, 6000);

    if (res.ok) {

      const data = await res.json();

      currentUser = data.user;

      renderAuthUI(currentUser);

    } else {

      currentUser = null;

      renderAuthUI(null);

    }

  } catch (err) {

    console.warn("Auth check failed:", err);

    currentUser = null;

    renderAuthUI(null);

  }

}



function renderAuthUI(user) {

  const loggedOutGroup = document.getElementById("auth-logged-out");

  const loggedInGroup = document.getElementById("auth-logged-in");

  const quotaSignInBtn = document.getElementById("quota-modal-signin-btn");



  if (user) {

    if (loggedOutGroup) loggedOutGroup.style.display = "none";

    if (loggedInGroup) loggedInGroup.style.display = "flex";

    if (quotaSignInBtn) quotaSignInBtn.style.display = "none";



    const name = user.full_name || (user.email ? user.email.split("@")[0] : "User");

    const initials = name.split(" ").map(p => p[0]).join("").toUpperCase().slice(0, 2) || "U";

    const avatarEl = document.getElementById("user-avatar-initials");

    const nameEl = document.getElementById("user-display-name");

    const dropNameEl = document.getElementById("user-dropdown-full-name");

    const dropEmailEl = document.getElementById("user-dropdown-email");

    const tierBadge = document.getElementById("user-tier-badge");

    const dropTierBadge = document.getElementById("user-dropdown-tier-badge");

    const upgradeBtn = document.getElementById("menu-upgrade-btn");

    const portalBtn = document.getElementById("menu-portal-btn");



    if (avatarEl) {

      if (user.avatar_url) {

        avatarEl.innerHTML = `<img src="${user.avatar_url}" alt="${name}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;" referrerpolicy="no-referrer">`;

      } else {

        avatarEl.innerText = initials;

      }

    }

    if (nameEl) nameEl.innerText = name.split(" ")[0];

    if (dropNameEl) dropNameEl.innerText = name;

    if (dropEmailEl) dropEmailEl.innerText = user.email;



    const isPro = (user.tier === "pro" || user.tier === "enterprise");

    if (tierBadge) {

      tierBadge.innerText = user.tier.toUpperCase();

      tierBadge.classList.toggle("pro", isPro);

    }

    if (dropTierBadge) {

      dropTierBadge.innerText = `${user.tier.toUpperCase()} PLAN`;

      dropTierBadge.classList.toggle("pro", isPro);

    }



    if (upgradeBtn) upgradeBtn.style.display = isPro ? "none" : "flex";

    if (portalBtn) portalBtn.style.display = isPro ? "flex" : "none";



    updateUserQuotaUI({

      tier: user.tier,

      used_today: user.used_today,

      limit: isPro ? "Unlimited" : 5,

      remaining: isPro ? "Unlimited" : Math.max(0, 5 - (user.used_today || 0))

    });



    const apiKeyInput = document.getElementById("user-api-key-input");

    const curlKeyPlaceholder = document.getElementById("curl-key-placeholder");

    if (apiKeyInput) apiKeyInput.value = user.api_key || "ilf_live_demo_key";

    if (curlKeyPlaceholder) curlKeyPlaceholder.innerText = user.api_key || "ilf_live_demo_key";



    const freeCardBtn = document.getElementById("btn-plan-free");

    const proCardBtn = document.getElementById("btn-plan-pro");

    if (freeCardBtn) {

      if (user.tier === "free") {

        freeCardBtn.innerText = "Current Plan";

        freeCardBtn.disabled = true;

      } else {

        freeCardBtn.innerText = "Downgrade";

        freeCardBtn.disabled = false;

      }

    }

    if (proCardBtn) {

      if (user.tier === "pro") {

        proCardBtn.innerText = "Active Plan (Pro)";

        proCardBtn.disabled = true;

      } else {

        proCardBtn.innerHTML = `<span>Upgrade to Pro</span><i data-lucide="zap" style="width: 16px; height: 16px;"></i>`;

        proCardBtn.disabled = false;

      }

    }

  } else {

    if (loggedOutGroup) loggedOutGroup.style.display = "inline-flex";

    if (loggedInGroup) loggedInGroup.style.display = "none";

    if (quotaSignInBtn) quotaSignInBtn.style.display = "block";



    const freeCardBtn = document.getElementById("btn-plan-free");

    if (freeCardBtn) {

      freeCardBtn.innerText = "Start Free";

      freeCardBtn.disabled = false;

    }

  }

  if (window.lucide) lucide.createIcons();

}



function updateUserQuotaUI(quota) {

  const quotaText = document.getElementById("user-quota-text");

  const quotaFill = document.getElementById("user-quota-fill");

  if (!quotaText || !quotaFill) return;



  const isPro = (quota.tier === "pro" || quota.tier === "enterprise" || quota.limit === "Unlimited" || quota.limit === null);

  if (isPro) {

    quotaText.innerText = "Unlimited Tasks";

    quotaFill.style.width = "100%";

    quotaFill.classList.add("unlimited");

  } else {

    const used = quota.used_today || 0;

    const limit = quota.limit || 5;

    quotaText.innerText = `${used} / ${limit} used`;

    const pct = Math.min(100, Math.round((used / limit) * 100));

    quotaFill.style.width = `${pct}%`;

    quotaFill.classList.remove("unlimited");

  }

}



// User Menu Dropdown Toggle

function toggleUserDropdown(forceState) {

  const menu = document.getElementById("user-dropdown-menu");

  if (!menu) return;

  const isHidden = (menu.style.display === "none" || menu.style.display === "");

  const newState = (forceState !== undefined) ? forceState : isHidden;

  menu.style.display = newState ? "block" : "none";



  if (newState) {

    setTimeout(() => {

      const closeHandler = (e) => {

        if (!e.target.closest(".user-profile-wrap")) {

          menu.style.display = "none";

          document.removeEventListener("click", closeHandler);

        }

      };

      document.addEventListener("click", closeHandler);

    }, 10);

  }

}



// Modals Handling

function openModal(modalId) {

  const el = document.getElementById(modalId);

  if (el) {

    el.style.display = "flex";

    document.body.style.overflow = "hidden";

    if (window.lucide) lucide.createIcons();

  }

}



function closeModal(modalId) {

  const el = document.getElementById(modalId);

  if (el) {

    el.style.display = "none";

    document.body.style.overflow = "";

  }

}



function handleBackdropClick(event, modalId) {

  if (event.target && event.target.id === modalId) {

    closeModal(modalId);

  }

}



// Auth Modal

function openAuthModal(tab = 'signin') {

  openModal('modal-auth');

  switchAuthTab(tab);

}



function switchAuthTab(tab) {

  const signinBtn = document.getElementById('auth-tab-signin-btn');

  const signupBtn = document.getElementById('auth-tab-signup-btn');

  const signinForm = document.getElementById('auth-signin-form');

  const signupForm = document.getElementById('auth-signup-form');

  const modalTitle = document.getElementById('auth-modal-title');

  const modalSubtitle = document.getElementById('auth-modal-subtitle');

  const errorMsg = document.getElementById('auth-error-msg');



  if (errorMsg) errorMsg.style.display = 'none';



  if (tab === 'signin') {

    if (signinBtn) signinBtn.classList.add('active');

    if (signupBtn) signupBtn.classList.remove('active');

    if (signinForm) signinForm.style.display = 'block';

    if (signupForm) signupForm.style.display = 'none';

    if (modalTitle) modalTitle.innerText = "Welcome back to I LOVE FILES";

    if (modalSubtitle) modalSubtitle.innerText = "Sign in to access your free daily conversions & history";

  } else {

    if (signinBtn) signinBtn.classList.remove('active');

    if (signupBtn) signupBtn.classList.add('active');

    if (signinForm) signinForm.style.display = 'none';

    if (signupForm) signupForm.style.display = 'block';

    if (modalTitle) modalTitle.innerText = "Create Your Free Account";

    if (modalSubtitle) modalSubtitle.innerText = "Get 5 free conversions every day & local-first privacy";

  }

  if (window.lucide) lucide.createIcons();

}



function showAuthError(msg) {

  const banner = document.getElementById('auth-error-msg');

  if (banner) {

    banner.innerText = msg;

    banner.style.display = 'block';

  }

}



// Google One-Click OAuth Implementation

async function initGoogleAuth() {

  try {

    const cfgRes = await fetchWithTimeout("/api/auth/config", {}, 4000);

    if (cfgRes.ok) {

      const cfg = await cfgRes.json();

      if (cfg.google_client_id) googleClientId = cfg.google_client_id;

    }

  } catch (e) {}



  function setupGSI() {

    if (typeof google === 'undefined' || !google.accounts || !google.accounts.id) return;

    try {

      google.accounts.id.initialize({

        client_id: googleClientId,

        callback: handleGoogleCredentialResponse,

        auto_select: false,

        cancel_on_tap_outside: true

      });

      googleAuthInitialized = true;

      const wrap = document.getElementById('google-native-btn-wrap');

      if (wrap) {

        google.accounts.id.renderButton(wrap, {

          theme: 'outline',

          size: 'large',

          width: 320,

          text: 'continue_with'

        });

      }

    } catch (err) {

      console.warn("GSI initialization error:", err);

    }

  }



  if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {

    setupGSI();

  } else {

    window.addEventListener('load', () => setTimeout(setupGSI, 500));

  }

}



function triggerGoogleSignIn() {

  const errorMsg = document.getElementById('auth-error-msg');

  if (errorMsg) errorMsg.style.display = 'none';



  if (window.location.protocol === 'file:') {

    showAuthError("Please run the app via http://localhost:8000 to use Google Sign-In.");

    return;

  }



  if (typeof google === 'undefined' || !google.accounts || !google.accounts.id) {

    showAuthError("Google Sign-In is loading or blocked by your browser/ad-blocker. Please allow accounts.google.com or use email sign in below.");

    return;

  }



  if (!googleAuthInitialized) {

    try {

      google.accounts.id.initialize({

        client_id: googleClientId,

        callback: handleGoogleCredentialResponse,

        auto_select: false,

        cancel_on_tap_outside: true

      });

      googleAuthInitialized = true;

    } catch (e) {

      console.error(e);

    }

  }



  try {

    google.accounts.id.prompt((notification) => {

      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {

        const wrap = document.getElementById('google-native-btn-wrap');

        if (wrap) {

          const btn = wrap.querySelector('div[role="button"]') || wrap.querySelector('iframe');

          if (btn) {

            btn.click();

          } else {

            wrap.style.display = 'block';

            const customBtn = document.getElementById('btn-google-auth');

            if (customBtn) customBtn.style.display = 'none';

          }

        }

      }

    });

  } catch (err) {

    console.error("Google prompt failed:", err);

    showAuthError("Could not launch Google Sign-In prompt. Please ensure popups are enabled or sign in with email.");

  }

}



async function handleGoogleCredentialResponse(response) {

  if (!response || !response.credential) {

    showAuthError("Google Sign-In was cancelled or failed.");

    return;

  }

  const googleBtn = document.getElementById('btn-google-auth');

  const googleBtnText = document.getElementById('google-btn-text');

  if (googleBtn) googleBtn.disabled = true;

  if (googleBtnText) googleBtnText.innerText = "Signing in with Google...";



  try {

    const res = await fetchWithTimeout("/api/auth/google", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ credential: response.credential })

    }, 15000);

    const data = await res.json();

    if (!res.ok) {

      throw new Error(data.detail || "Google Sign-In failed on server.");

    }



    currentUser = data.user;

    renderAuthUI(currentUser);

    closeModal('modal-auth');

    if (window.showToast) {

      showToast(`Welcome, ${currentUser.full_name || currentUser.email}!`, 'success');

    }

  } catch (err) {

    showAuthError(err.message || "Failed to sign in with Google.");

  } finally {

    if (googleBtn) googleBtn.disabled = false;

    if (googleBtnText) googleBtnText.innerText = "Continue with Google";

  }

}



async function handleSignInSubmit(e) {

  e.preventDefault();

  const email = document.getElementById('auth-signin-email')?.value?.trim();

  const password = document.getElementById('auth-signin-password')?.value;

  const submitBtn = document.getElementById('btn-submit-signin');



  if (!email || !password) {

    showAuthError("Please provide both email and password.");

    return;

  }



  if (submitBtn) { submitBtn.disabled = true; submitBtn.innerText = "Signing in..."; }



  try {

    const res = await fetchWithTimeout("/api/auth/signin", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ email, password })

    }, 10000);

    const data = await res.json();

    if (!res.ok) {

      throw new Error(data.detail || "Sign in failed");

    }



    currentUser = data.user;

    renderAuthUI(currentUser);

    closeModal('modal-auth');

  } catch (err) {

    showAuthError(err.message);

  } finally {

    if (submitBtn) {

      submitBtn.disabled = false;

      submitBtn.innerHTML = `<span>Sign In</span><i data-lucide="arrow-right" style="width: 16px; height: 16px;"></i>`;

      if (window.lucide) lucide.createIcons();

    }

  }

}



async function handleSignUpSubmit(e) {

  e.preventDefault();

  const fullName = document.getElementById('auth-signup-name')?.value?.trim();

  const email = document.getElementById('auth-signup-email')?.value?.trim();

  const password = document.getElementById('auth-signup-password')?.value;

  const submitBtn = document.getElementById('btn-submit-signup');



  if (!email || !password) {

    showAuthError("Please fill out all required fields.");

    return;

  }



  if (password.length < 8) {

    showAuthError("Password must be at least 8 characters long.");

    return;

  }



  if (submitBtn) { submitBtn.disabled = true; submitBtn.innerText = "Creating account..."; }



  try {

    const res = await fetchWithTimeout("/api/auth/signup", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ email, password, full_name: fullName })

    }, 10000);

    const data = await res.json();

    if (!res.ok) {

      throw new Error(data.detail || "Sign up failed");

    }



    currentUser = data.user;

    renderAuthUI(currentUser);

    closeModal('modal-auth');

  } catch (err) {

    showAuthError(err.message);

  } finally {

    if (submitBtn) {

      submitBtn.disabled = false;

      submitBtn.innerHTML = `<span>Create Free Account</span><i data-lucide="check" style="width: 16px; height: 16px;"></i>`;

      if (window.lucide) lucide.createIcons();

    }

  }

}



async function handleSignOut() {

  toggleUserDropdown(false);

  try {

    await fetch("/api/auth/signout", { method: "POST" });

  } catch (e) {}

  currentUser = null;

  renderAuthUI(null);

}



// Pricing & Checkout

function openPricingModal() {

  toggleUserDropdown(false);

  openModal('modal-pricing');

}



function toggleBillingCycle() {

  billingAnnual = !billingAnnual;

  const switchBtn = document.getElementById("billing-cycle-switch");

  const labelMonthly = document.getElementById("label-cycle-monthly");

  const labelAnnual = document.getElementById("label-cycle-annual");



  const priceProAmt = document.getElementById("price-pro-amt");

  const priceProSub = document.getElementById("price-pro-sub");

  const priceProAnnualSub = document.getElementById("price-pro-annual-sub");



  const priceEntAmt = document.getElementById("price-enterprise-amt");

  const priceEntSub = document.getElementById("price-enterprise-sub");

  const priceEntAnnualSub = document.getElementById("price-enterprise-annual-sub");



  if (switchBtn) switchBtn.classList.toggle("annual", billingAnnual);

  if (labelMonthly) labelMonthly.classList.toggle("active", !billingAnnual);

  if (labelAnnual) labelAnnual.classList.toggle("active", billingAnnual);



  if (billingAnnual) {

    if (priceProAmt) priceProAmt.innerText = "₹333";

    if (priceProSub) priceProSub.innerText = "/ month";

    if (priceProAnnualSub) priceProAnnualSub.style.display = "block";



    if (priceEntAmt) priceEntAmt.innerText = "₹1,333";

    if (priceEntSub) priceEntSub.innerText = "/ month";

    if (priceEntAnnualSub) priceEntAnnualSub.style.display = "block";

  } else {

    if (priceProAmt) priceProAmt.innerText = "₹499";

    if (priceProSub) priceProSub.innerText = "/ month";

    if (priceProAnnualSub) priceProAnnualSub.style.display = "none";



    if (priceEntAmt) priceEntAmt.innerText = "₹1,999";

    if (priceEntSub) priceEntSub.innerText = "/ month";

    if (priceEntAnnualSub) priceEntAnnualSub.style.display = "none";

  }

}



function handleFreePlanAction() {

  if (!currentUser) {

    closeModal('modal-pricing');

    openAuthModal('signup');

  } else {

    closeModal('modal-pricing');

  }

}



async function startCheckout(tier) {

  if (!currentUser) {

    closeModal('modal-pricing');

    openAuthModal('signup');

    return;

  }



  const interval = billingAnnual ? 'year' : 'month';

  try {

    const res = await fetchWithTimeout("/api/billing/create-checkout-session", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ tier, interval })

    }, 15000);

    const data = await res.json();

    if (!res.ok) {

      throw new Error(data.detail || "Unable to start checkout");

    }



    if (data.mode === "cashfree" && data.payment_session_id) {

      closeModal('modal-pricing');

      if (window.Cashfree) {

        const cashfree = window.Cashfree({ mode: data.environment || "sandbox" });

        cashfree.checkout({

          paymentSessionId: data.payment_session_id,

          redirectTarget: "_modal"

        }).then((result) => {

          if (result && result.error) {

            alert("Payment Error: " + (result.error.message || "Failed"));

          }

          verifyCashfreePayment(data.order_id);

        }).catch(() => {

          verifyCashfreePayment(data.order_id);

        });



        // Background polling to auto-detect payment completion

        let pollCount = 0;

        const pollInterval = setInterval(async () => {

          pollCount++;

          if (pollCount > 12 || (currentUser && (currentUser.tier === "pro" || currentUser.tier === "enterprise"))) {

            clearInterval(pollInterval);

            return;

          }

          try {

            const pollRes = await fetch(`/api/billing/verify-payment?order_id=${encodeURIComponent(data.order_id)}`);

            const pollData = await pollRes.json();

            if (pollData.status === "success") {

              clearInterval(pollInterval);

              if (currentUser) currentUser.tier = pollData.tier;

              await initAuth();

              showToast("🎉 Payment verified! PRO tier is active.", "success");

            }

          } catch (e) {}

        }, 2500);

      } else {

        verifyCashfreePayment(data.order_id);

      }

    } else if (data.mode === "demo") {

      currentUser.tier = data.tier;

      renderAuthUI(currentUser);

      closeModal('modal-pricing');

      alert(`🎉 DEMO MODE ACTIVATED!\n\nYou have been upgraded to the ${data.tier.toUpperCase()} tier for 30 days!\nEnjoy unlimited file conversions and AutoCAD batch plotting.`);

    }

  } catch (err) {

    alert(`Checkout Error: ${err.message}`);

  }

}



async function instantDemoUpgrade(tier) {

  if (!currentUser) {

    closeModal('modal-pricing');

    openAuthModal('signup');

    return;

  }

  try {

    const res = await fetch("/api/billing/demo-toggle-tier", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ tier: tier || "pro" })

    });

    const data = await res.json();

    if (res.ok && data.status === "success") {

      currentUser.tier = data.tier;

      renderAuthUI(currentUser);

      closeModal('modal-pricing');

      showToast(`🎉 Your account has been upgraded to ${data.tier.toUpperCase()} (Unlimited conversions & AutoCAD plotting active)!`, "success");

      await initAuth();

    } else {

      showToast(data.detail || "Upgrade failed", "error");

    }

  } catch (e) {

    showToast(e.message, "error");

  }

}



async function verifyCashfreePayment(orderId) {

  try {

    const res = await fetchWithTimeout(`/api/billing/verify-payment?order_id=${encodeURIComponent(orderId)}`, {}, 15000);

    const data = await res.json();

    if (data.status === "success") {

      if (currentUser) currentUser.tier = data.tier;

      await initAuth();

      alert("🎉 Payment Successful!\n\nYour account has been upgraded to PRO! Enjoy unlimited daily conversions and AutoCAD batch plotting.");

    } else {

      console.log("Cashfree payment verification status:", data);

    }

  } catch (err) {

    console.error("Failed to verify payment:", err);

  }

}



async function openBillingPortal() {

  toggleUserDropdown(false);

  try {

    const res = await fetch("/api/billing/customer-portal", { method: "POST" });

    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "Cannot access portal");

    if (data.url) {

      window.location.href = data.url;

    } else {

      alert(data.message || "Subscription portal is not configured in Demo Mode.");

    }

  } catch (err) {

    alert(`Billing Portal: ${err.message}`);

  }

}



function openApiKeyModal() {

  toggleUserDropdown(false);

  if (!currentUser) {

    openAuthModal('signin');

    return;

  }

  openModal('modal-api-key');

}



function copyApiKey() {

  const input = document.getElementById("user-api-key-input");

  const btn = document.getElementById("btn-copy-api-key");

  if (!input || !input.value) return;



  navigator.clipboard.writeText(input.value).then(() => {

    if (btn) {

      btn.innerHTML = `<i data-lucide="check" style="width: 15px; height: 15px; color: #10b981;"></i><span>Copied!</span>`;

      if (window.lucide) lucide.createIcons();

      setTimeout(() => {

        btn.innerHTML = `<i data-lucide="copy" style="width: 15px; height: 15px;"></i><span>Copy</span>`;

        if (window.lucide) lucide.createIcons();

      }, 2000);

    }

  }).catch(() => {

    input.select();

    document.execCommand("copy");

  });

}



function showQuotaLimitModal(customMsg) {

  if (customMsg) {

    const msgEl = document.getElementById("quota-limit-msg");

    if (msgEl) msgEl.innerText = customMsg;

  }

  openModal('modal-quota-limit');

}



// -------------------------------------------------------------

// Interactive Command Search (⌘K / Ctrl+K)

// -------------------------------------------------------------

function focusHubSearch() {

  switchTab('convert');

  setTimeout(() => {

    const input = document.getElementById('hub-search-input');

    if (input) {

      input.removeAttribute('readonly');

      input.focus();

      input.select();

      input.scrollIntoView({ behavior: 'smooth', block: 'center' });

    }

  }, 50);

}



document.addEventListener('keydown', (e) => {

  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {

    e.preventDefault();

    focusHubSearch();

  }

});



// -------------------------------------------------------------

// Cookie & Local Storage Consent Banner Logic

// -------------------------------------------------------------

function initCookieConsent() {

  try {

    const consent = localStorage.getItem("ilovefiles_cookie_consent");

    if (!consent) {

      const banner = document.getElementById("cookie-consent-banner");

      if (banner) {

        setTimeout(() => {

          banner.style.display = "block";

          if (window.lucide) lucide.createIcons();

        }, 600);

      }

    }

  } catch (e) {}

}



function acceptCookieConsent() {

  try {

    localStorage.setItem("ilovefiles_cookie_consent", "accepted");

  } catch (e) {}

  const banner = document.getElementById("cookie-consent-banner");

  if (banner) {

    banner.style.display = "none";

  }

}



// Auto-run cookie consent check on DOM ready

if (document.readyState === "loading") {

  document.addEventListener("DOMContentLoaded", initCookieConsent);

} else {

  initCookieConsent();

}



// =============================================================

// HERO LANDING STUDIO CONTROLLER (AutoCAD & Universal)

// =============================================================



let landingStudioMode = 'autocad'; // 'autocad' | 'universal'

let landingStudioFiles = [];

let landingCustomCtbFile = null;

let landingStudioPresets = {

  printer: "AutoCAD PDF (High Quality Print).pc3",

  paperSize: "ANSI full bleed B (17.00 x 11.00 Inches)",

  plotArea: "Extents",

  shadePlot: "Wireframe",

  orientation: "Landscape",

  fitToPaper: true,

  centerPlot: true,

  plotLineweights: true,

  plotStyles: true,

  mergeOutput: true

};



function handleLandingCtbSelect(files) {

  if (!files || !files.length) return;

  const file = files[0];

  if (!file.name.toLowerCase().endsWith('.ctb')) {

    alert("Please select an AutoCAD plot style table (.ctb file).");

    return;

  }

  landingCustomCtbFile = file;

  const badge = document.getElementById("landing-ctb-attached-badge");

  const nameEl = document.getElementById("landing-ctb-attached-name");

  if (badge && nameEl) {

    nameEl.innerText = file.name;

    badge.style.display = "inline-flex";

  }

}



function clearLandingCustomCtb() {

  landingCustomCtbFile = null;

  const badge = document.getElementById("landing-ctb-attached-badge");

  if (badge) badge.style.display = "none";

  const input = document.getElementById("landing-ctb-file");

  if (input) input.value = "";

}



function initLandingStudio() {

  const dropzone = document.getElementById("landing-main-dropzone");

  const fileInput = document.getElementById("landing-main-file-input");



  if (fileInput) {

    fileInput.addEventListener("click", (e) => {

      e.stopPropagation();

    });

  }



  if (dropzone) {

    ['dragenter', 'dragover'].forEach(evt => {

      dropzone.addEventListener(evt, (e) => {

        e.preventDefault();

        e.stopPropagation();

        dropzone.classList.add('dragover');

      });

    });

    ['dragleave', 'drop'].forEach(evt => {

      dropzone.addEventListener(evt, (e) => {

        e.preventDefault();

        e.stopPropagation();

        dropzone.classList.remove('dragover');

      });

    });

    dropzone.addEventListener('drop', (e) => {

      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {

        handleLandingFilesSelected(e.dataTransfer.files);

      }

    });

  }



  const presetModal = document.getElementById("landing-preset-modal");

  if (presetModal) {

    presetModal.addEventListener("click", (e) => {

      if (e.target === presetModal) closeLandingPresetModal();

    });

  }

}



function setLandingMode(mode) {

  landingStudioMode = mode;

  const cadPill = document.getElementById("tab-mode-autocad");

  const uniPill = document.getElementById("tab-mode-universal");

  const ctbWrap = document.getElementById("landing-ctb-selector-wrap");

  const uniWrap = document.getElementById("landing-universal-target-wrap");

  const presetsBar = document.getElementById("landing-presets-bar");



  if (cadPill && uniPill) {

    if (mode === 'autocad') {

      cadPill.classList.add('active');

      uniPill.classList.remove('active');

      if (ctbWrap) ctbWrap.style.display = 'flex';

      if (uniWrap) uniWrap.style.display = 'none';

      if (presetsBar) presetsBar.style.display = 'flex';

    } else {

      uniPill.classList.add('active');

      cadPill.classList.remove('active');

      if (ctbWrap) ctbWrap.style.display = 'none';

      if (uniWrap) uniWrap.style.display = 'flex';

      if (presetsBar) presetsBar.style.display = 'none';

    }

  }

  updateLandingQueueUI();

}



function handleLandingFilesSelected(fileList) {

  if (!fileList || !fileList.length) return;

  const newFiles = Array.from(fileList);



  // Auto-detect if CAD files are present

  const hasCadFiles = newFiles.some(f => {

    const ext = f.name.split('.').pop().toLowerCase();

    return ext === 'dwg' || ext === 'dxf';

  });



  if (hasCadFiles && landingStudioMode !== 'autocad') {

    setLandingMode('autocad');

  }



  landingStudioFiles = landingStudioFiles.concat(newFiles);

  updateLandingQueueUI();
  updateCloudEgressMetric();



  const input = document.getElementById("landing-main-file-input");

  if (input) input.value = "";

}



function removeLandingFile(idx) {

  if (idx >= 0 && idx < landingStudioFiles.length) {

    landingStudioFiles.splice(idx, 1);

    updateLandingQueueUI();
    updateCloudEgressMetric();

  }

}



function clearLandingQueue() {

  landingStudioFiles = [];

  updateLandingQueueUI();
  updateCloudEgressMetric();

  const resWrap = document.getElementById("landing-queue-result-wrap");

  if (resWrap) resWrap.style.display = "none";

}



function resetLandingQueue() {

  landingStudioFiles = [];

  updateLandingQueueUI();
  updateCloudEgressMetric();

  const resWrap = document.getElementById("landing-queue-result-wrap");

  if (resWrap) resWrap.style.display = "none";

}



function escapeLandingHtml(str) {

  if (!str) return '';

  return String(str)

    .replace(/&/g, '&amp;')

    .replace(/</g, '&lt;')

    .replace(/>/g, '&gt;')

    .replace(/"/g, '&quot;')

    .replace(/'/g, '&#039;');

}



function updateLandingQueueUI() {

  const container = document.getElementById("landing-staged-items-container");

  const countBadge = document.getElementById("landing-queue-count-badge");

  const convertBtn = document.getElementById("landing-convert-btn");

  const btnText = document.getElementById("landing-convert-btn-text");



  const count = landingStudioFiles.length;

  if (countBadge) {

    countBadge.innerText = `${count} Staged`;

  }



  if (count === 0) {

    if (container) {

      container.innerHTML = `

        <div id="landing-queue-empty-msg" class="queue-empty-box">

          No drawings in queue. Drag &amp; drop AutoCAD DWG/DXF or documents above to begin.

        </div>

      `;

    }

    if (convertBtn) convertBtn.disabled = true;

    if (btnText) {

      btnText.innerText = landingStudioMode === 'autocad'

        ? "Execute AutoCAD Batch Plot (0 Files)"

        : "Convert Files (0 Files)";

    }

    return;

  }



  if (convertBtn) convertBtn.disabled = false;

  if (btnText) {

    if (landingStudioMode === 'autocad') {

      btnText.innerText = `Execute AutoCAD Batch Plot (${count} File${count > 1 ? 's' : ''})`;

    } else {

      const tgt = document.getElementById("landing-universal-target-select")?.value?.toUpperCase() || "PDF";

      btnText.innerText = `Convert ${count} File${count > 1 ? 's' : ''} to ${tgt}`;

    }

  }



  if (container) {

    container.innerHTML = landingStudioFiles.map((file, idx) => {

      const ext = file.name.split('.').pop().toLowerCase();

      const isCad = ext === 'dwg' || ext === 'dxf';

      const badgeClass = isCad ? 'badge-tag-cad' : 'badge-tag-doc';

      return `

        <div class="staged-row">

          <div class="staged-left">

            <span class="staged-num">${idx + 1}.</span>

            <span class="${badgeClass}">.${ext.toUpperCase()}</span>

            <span class="staged-name" title="${escapeLandingHtml(file.name)}">${escapeLandingHtml(file.name)}</span>

            <span class="staged-size">${formatBytes(file.size)}</span>

          </div>

          <button type="button" class="staged-remove-btn" onclick="removeLandingFile(${idx})" title="Remove file" aria-label="Remove file">

            <span class="material-symbols-outlined" style="font-size: 15px;">close</span>

          </button>

        </div>

      `;

    }).join("");

  }

}



function openLandingPresetModal() {

  const modal = document.getElementById("landing-preset-modal");

  if (modal) {

    // Populate controls with current preset values

    const printerEl = document.getElementById("modal-landing-printer");

    const paperEl = document.getElementById("modal-landing-paper-size");

    const areaEl = document.getElementById("modal-landing-plot-area");

    const shadeEl = document.getElementById("modal-landing-shade");

    const orientEl = document.getElementById("modal-landing-orientation");

    const fitEl = document.getElementById("modal-landing-fit");

    const centerEl = document.getElementById("modal-landing-center");

    const lineweightsEl = document.getElementById("modal-landing-lineweights");

    const stylesEl = document.getElementById("modal-landing-styles");

    const mergeEl = document.getElementById("modal-landing-merge-output");



    if (printerEl && landingStudioPresets.printer) printerEl.value = landingStudioPresets.printer;

    if (paperEl && landingStudioPresets.paperSize) paperEl.value = landingStudioPresets.paperSize;

    if (areaEl && landingStudioPresets.plotArea) areaEl.value = landingStudioPresets.plotArea;

    if (shadeEl && landingStudioPresets.shadePlot) shadeEl.value = landingStudioPresets.shadePlot;

    if (orientEl && landingStudioPresets.orientation) orientEl.value = landingStudioPresets.orientation;

    if (fitEl) fitEl.checked = landingStudioPresets.fitToPaper !== false;

    if (centerEl) centerEl.checked = landingStudioPresets.centerPlot !== false;

    if (lineweightsEl) lineweightsEl.checked = landingStudioPresets.plotLineweights !== false;

    if (stylesEl) stylesEl.checked = landingStudioPresets.plotStyles !== false;

    if (mergeEl) mergeEl.checked = landingStudioPresets.mergeOutput !== false;



    modal.style.display = "flex";

  }

}



function closeLandingPresetModal() {

  const modal = document.getElementById("landing-preset-modal");

  if (modal) modal.style.display = "none";

}



function saveLandingPresets() {

  const printer = document.getElementById("modal-landing-printer")?.value;

  const paper = document.getElementById("modal-landing-paper-size")?.value;

  const area = document.getElementById("modal-landing-plot-area")?.value;

  const shade = document.getElementById("modal-landing-shade")?.value;

  const orient = document.getElementById("modal-landing-orientation")?.value;

  const fit = document.getElementById("modal-landing-fit")?.checked;

  const center = document.getElementById("modal-landing-center")?.checked;

  const lineweights = document.getElementById("modal-landing-lineweights")?.checked;

  const styles = document.getElementById("modal-landing-styles")?.checked;

  const merge = document.getElementById("modal-landing-merge-output")?.checked;



  if (printer) landingStudioPresets.printer = printer;

  if (paper) landingStudioPresets.paperSize = paper;

  if (area) landingStudioPresets.plotArea = area;

  if (shade) landingStudioPresets.shadePlot = shade;

  if (orient) landingStudioPresets.orientation = orient;

  if (fit !== undefined) landingStudioPresets.fitToPaper = fit;

  if (center !== undefined) landingStudioPresets.centerPlot = center;

  if (lineweights !== undefined) landingStudioPresets.plotLineweights = lineweights;

  if (styles !== undefined) landingStudioPresets.plotStyles = styles;

  if (merge !== undefined) landingStudioPresets.mergeOutput = merge;



  // Update label

  const paperLabel = document.getElementById("landing-preset-paper-label");

  if (paperLabel && paper) {

    let shortLabel = "ANSI B (11x17)";

    if (paper.includes("ANSI full bleed B") || paper.includes("ANSI B")) shortLabel = "ANSI B (11x17)";

    else if (paper.includes("A0")) shortLabel = "ISO A0";

    else if (paper.includes("A1")) shortLabel = "ISO A1 (Arch D)";

    else if (paper.includes("A2")) shortLabel = "ISO A2";

    else if (paper.includes("A3")) shortLabel = "ISO A3";

    else if (paper.includes("A4")) shortLabel = "ISO A4";

    else if (paper.includes("ARCH full bleed D")) shortLabel = "ARCH D (24x36)";

    paperLabel.innerText = shortLabel;

  }



  closeLandingPresetModal();

}



// =============================================================

// PROCESS HEART REFINERY HUD CONTROLLER

// =============================================================

let hudTimer = null;

let hudStartTime = 0;



function startProcessingHud({ title, subtitle, badgeText = "AUTOCAD 2026 CORE REFINERY" }) {

  const modal = document.getElementById("ilf-processing-modal");

  if (!modal) return;



  const titleEl = document.getElementById("ilf-proc-title");

  const subEl = document.getElementById("ilf-proc-subtext");

  const badgeEl = document.getElementById("ilf-proc-badge-text");

  const barEl = document.getElementById("ilf-proc-bar-fill");

  const pctEl = document.getElementById("ilf-proc-pct");

  const sheetsEl = document.getElementById("ilf-proc-sheets");



  if (titleEl) titleEl.innerText = title || "Vector Plotting & Compiling...";

  if (subEl) subEl.innerText = subtitle || "Staging models & applying CTB pen table...";

  if (badgeEl) badgeEl.innerText = badgeText;

  if (barEl) barEl.style.width = "12%";

  if (pctEl) pctEl.innerText = "12%";

  if (sheetsEl) sheetsEl.innerText = "0.0s elapsed";



  modal.style.display = "flex";

  hudStartTime = Date.now();



  if (hudTimer) clearInterval(hudTimer);

  hudTimer = setInterval(() => {

    const elapsed = ((Date.now() - hudStartTime) / 1000).toFixed(1);

    if (sheetsEl) sheetsEl.innerText = `${elapsed}s elapsed`;

  }, 200);

}



function updateProcessingHud(pct, subtext, title) {

  const barEl = document.getElementById("ilf-proc-bar-fill");

  const pctEl = document.getElementById("ilf-proc-pct");

  const subEl = document.getElementById("ilf-proc-subtext");

  const titleEl = document.getElementById("ilf-proc-title");



  if (barEl) barEl.style.width = `${pct}%`;

  if (pctEl) pctEl.innerText = `${pct}%`;

  if (subEl && subtext) subEl.innerText = subtext;

  if (titleEl && title) titleEl.innerText = title;

}



function stopProcessingHud(callback) {

  if (hudTimer) {

    clearInterval(hudTimer);

    hudTimer = null;

  }

  const modal = document.getElementById("ilf-processing-modal");

  const barEl = document.getElementById("ilf-proc-bar-fill");

  const pctEl = document.getElementById("ilf-proc-pct");

  const subEl = document.getElementById("ilf-proc-subtext");



  if (barEl) barEl.style.width = "100%";

  if (pctEl) pctEl.innerText = "100%";

  if (subEl) subEl.innerText = "Vector compilation complete!";



  setTimeout(() => {

    if (modal) modal.style.display = "none";

    if (typeof callback === "function") callback();

  }, 450);

}



async function executeLandingConversion() {

  if (!landingStudioFiles.length) return;



  const btn = document.getElementById("landing-convert-btn");

  const btnText = document.getElementById("landing-convert-btn-text");

  const errBanner = document.getElementById("landing-queue-error-banner");

  const errText = document.getElementById("landing-queue-error-text");

  const resWrap = document.getElementById("landing-queue-result-wrap");



  if (errBanner) errBanner.style.display = "none";

  if (resWrap) resWrap.style.display = "none";



  btn.disabled = true;

  if (btnText) btnText.innerText = "Processing batch...";



  const hasCadFiles = landingStudioFiles.some(f => {

    const ext = f.name.split('.').pop().toLowerCase();

    return ext === 'dwg' || ext === 'dxf';

  });



  if (landingStudioMode === 'autocad' || hasCadFiles) {

    const ctbSelect = document.getElementById("landing-ctb-select");

    const ctb = landingCustomCtbFile ? landingCustomCtbFile.name : (ctbSelect?.value || "monochrome.ctb");

    const numFiles = landingStudioFiles.length;



    startProcessingHud({

      title: "AutoCAD Batch Plotting Engine",

      subtitle: `Staging ${numFiles} drawing(s) & applying ${ctb}...`,

      badgeText: "AUTOCAD 2026 CORE REFINERY"

    });



    let currentPct = 10;
    const tickMs = Math.max(350, Math.min(1500, Math.round((numFiles || 1) * 80)));
    const intervalTimer = setInterval(() => {
      if (currentPct < 96) {
        currentPct += (currentPct < 40 ? 5 : (currentPct < 80 ? 3 : 1));
        let stageMsg = `Staging ${numFiles} CAD drawings in parallel memory...`;
        if (currentPct > 20) stageMsg = `AutoCAD Multi-Core Engine: Plotting ${numFiles} sheets in parallel...`;
        if (currentPct > 55) stageMsg = `Applying ${ctb} pen tables, TrueColor & lineweights...`;
        if (currentPct > 80) stageMsg = `Compiling multi-page vector booklet & generating previews...`;
        updateProcessingHud(currentPct, stageMsg);
      }
    }, tickMs);



    const fd = new FormData();

    landingStudioFiles.forEach(f => fd.append("files", f));

    if (landingCustomCtbFile) {

      fd.append("ctb_file", landingCustomCtbFile);

    }



    fd.append("printer", landingStudioPresets.printer || "AutoCAD PDF (High Quality Print).pc3");

    fd.append("paper_size", landingStudioPresets.paperSize || "ANSI full bleed B (17.00 x 11.00 Inches)");

    fd.append("plot_style", ctb);

    fd.append("plot_area", landingStudioPresets.plotArea || "Extents");

    fd.append("center_plot", landingStudioPresets.centerPlot !== false);

    fd.append("fit_to_paper", landingStudioPresets.fitToPaper !== false);

    fd.append("orientation", landingStudioPresets.orientation || "Landscape");

    fd.append("plot_lineweights", landingStudioPresets.plotLineweights !== false);

    fd.append("plot_with_styles", landingStudioPresets.plotStyles !== false);

    fd.append("shade_plot", landingStudioPresets.shadePlot || "Wireframe");

    fd.append("merge_output", landingStudioPresets.mergeOutput !== false);



    const controller = new AbortController();

    const timeoutId = setTimeout(() => controller.abort(), 180000);



    try {

      const res = await fetch("/api/cad/batch-plot", {

        method: "POST",

        body: fd,

        signal: controller.signal

      });

      clearTimeout(timeoutId);

      clearInterval(intervalTimer);



      if (!res.ok) {

        const err = await res.json().catch(() => ({}));

        if (res.status === 429 || res.status === 403) {

          showQuotaLimitModal(err.detail || "AutoCAD batch plotting requires Pro subscription.");

        }

        throw new Error(err.detail || "AutoCAD batch plotting failed.");

      }



      const data = await res.json();

      if (data.quota && typeof updateUserQuotaUI === 'function') {

        updateUserQuotaUI(data.quota);

      }
      updateCloudEgressMetric(data.file_size || data.converted_bytes || 0, landingStudioFiles.length);



      stopProcessingHud(() => {

        btn.disabled = false;

        updateLandingQueueUI();



        if (resWrap) {

          const resTitle = document.getElementById("landing-result-title");

          const resMeta = document.getElementById("landing-result-meta");

          const dlBtn = document.getElementById("landing-result-download-btn");



          if (resTitle) resTitle.innerText = `Plotted ${data.sheets_plotted || landingStudioFiles.length} Sheet(s) Successfully!`;

          if (resMeta) resMeta.innerText = `${data.plot_style || ctb} • ${formatBytes(data.file_size || 0)} • ${(data.duration_ms / 1000).toFixed(1)}s • 100% Vector Fidelity`;

          if (dlBtn) {

            dlBtn.href = data.download_url;

            dlBtn.setAttribute("download", data.output_filename || "AutoCAD_Batch_Plot.pdf");

            dlBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px;">download</span><span>Download ${data.output_filename || 'Plotted PDF'}</span>`;

          }



          const previewContainer = document.getElementById("landing-plot-preview-container");

          const previewImg = document.getElementById("landing-plot-preview-img");

          const previewSource = data.preview_data_url || data.preview_url;

          if (previewSource && previewContainer && previewImg) {

            previewImg.src = previewSource;

            previewContainer.style.display = "block";

          } else if (previewContainer) {

            previewContainer.style.display = "none";

          }



          resWrap.style.display = "flex";

          resWrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        }

      });



    } catch (err) {

      clearInterval(intervalTimer);

      stopProcessingHud();

      btn.disabled = false;

      updateLandingQueueUI();

      if (errBanner && errText) {

        errText.innerText = err.message || "AutoCAD plotting failed. Please try again.";

        errBanner.style.display = "flex";

      }

    }



  } else {

    // Universal Conversion Mode

    const targetFormat = document.getElementById("landing-universal-target-select")?.value || "pdf";

    startProcessingHud({

      title: `Universal Format Converter (${targetFormat.toUpperCase()})`,

      subtitle: `Converting ${landingStudioFiles.length} file(s) locally...`,

      badgeText: "WASM SIMD CONVERSION CORE"

    });



    let currentPct = 20;

    const intervalTimer = setInterval(() => {

      if (currentPct < 88) {

        currentPct += 8;

        updateProcessingHud(currentPct, `Compiling vector data & document structures...`);

      }

    }, 300);



    try {

      let res;

      if (landingStudioFiles.length === 1) {

        const fd = new FormData();

        fd.append("file", landingStudioFiles[0]);

        fd.append("target_format", targetFormat);

        res = await fetch("/api/convert", { method: "POST", body: fd });

      } else {

        const fd = new FormData();

        landingStudioFiles.forEach(f => fd.append("files", f));

        fd.append("target_format", targetFormat);

        res = await fetch("/api/convert-batch", { method: "POST", body: fd });

      }



      clearInterval(intervalTimer);

      if (!res.ok) {

        const err = await res.json().catch(() => ({}));

        if (res.status === 429 || res.status === 403) {

          showQuotaLimitModal(err.detail || "Conversion limit reached.");

        }

        throw new Error(err.detail || "File conversion failed.");

      }



      const data = await res.json();

      if (data.quota && typeof updateUserQuotaUI === 'function') {

        updateUserQuotaUI(data.quota);

      }
      updateCloudEgressMetric(data.file_size || data.converted_bytes || 0, landingStudioFiles.length);



      stopProcessingHud(() => {

        btn.disabled = false;

        updateLandingQueueUI();

        if (resWrap) {

          const resTitle = document.getElementById("landing-result-title");

          const resMeta = document.getElementById("landing-result-meta");

          const dlBtn = document.getElementById("landing-result-download-btn");



          const outFilename = data.output_filename || data.filename || `converted_${targetFormat}`;

          const outSize = data.converted_bytes || data.converted_size || data.file_size || 0;

          if (resTitle) resTitle.innerText = `Conversion Complete!`;

          if (resMeta) resMeta.innerText = `${outFilename} • ${formatBytes(outSize)} • Local Zero Egress`;

          if (dlBtn) {

            dlBtn.href = data.download_url;

            dlBtn.setAttribute("download", outFilename);

            dlBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px;">download</span><span>Download ${outFilename}</span>`;

          }

          resWrap.style.display = "flex";

          resWrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        }

      });

    } catch (err) {

      clearInterval(intervalTimer);

      stopProcessingHud();

      btn.disabled = false;

      updateLandingQueueUI();

      if (errBanner && errText) {

        errText.innerText = err.message || "Conversion failed. Please try again.";

        errBanner.style.display = "flex";

      }

    }

  }

}



if (document.readyState !== "loading") {

  initLandingStudio();

} else {

  document.addEventListener("DOMContentLoaded", initLandingStudio);

}



// ============================================================================
// ALL PDF TOOLS MEGA MENU HANDLERS
// ============================================================================
function togglePdfMegaMenu(show) {
  const menu = document.getElementById("pdf-mega-menu");
  if (!menu) return;
  if (typeof show === "boolean") {
    menu.style.display = show ? "flex" : "none";
  } else {
    menu.style.display = (menu.style.display === "none" || !menu.style.display) ? "flex" : "none";
  }
  if (menu.style.display === "flex") {
    lucide.createIcons();
  }
}

// Close mega menu on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    togglePdfMegaMenu(false);
  }
});

function openQuickPdfTool(op) {
  togglePdfMegaMenu(false);
  
  if (op === 'merge') {
    switchTab('merge');
    return;
  }
  if (op === 'compress') {
    switchTab('resize');
    return;
  }
  
  // Switch to file converter tab and trigger tool in drawer
  switchTab('convert');
  const cardMap = {
    'split': 'card-split-pdf',
    'delete-pages': 'card-delete-pages',
    'rotate': 'card-rotate-pdf',
    'protect': 'card-protect-pdf',
    'unlock': 'card-unlock-pdf',
    'redact': 'card-redact-pdf',
    'pdf-to-word': 'card-pdf-to-word',
    'pdf-to-excel': 'card-pdf-to-excel',
    'pdf-to-pptx': 'card-pdf-to-pptx',
    'pdf-to-jpg': 'card-pdf-to-jpg',
    'pdf-to-png': 'card-pdf-to-png',
    'extract-images': 'card-extract-images',
    'pdf-to-pdfa': 'card-pdf-to-pdfa'
  };

  const cardId = cardMap[op];
  if (cardId && document.getElementById(cardId)) {
    document.getElementById(cardId).click();
  } else {
    // Directly activate contextual drawer for this operation
    selectQuickTool(op, op.replace(/-/g, ' ').toUpperCase(), '.pdf');
  }
  
  // Smooth scroll to drawer
  const drawer = document.getElementById("context-config-drawer");
  if (drawer) {
    drawer.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

function openAiTool(tool) {
  togglePdfMegaMenu(false);
  switchTab('ai');
  selectAiWorkspaceTool(tool);
}


// ============================================================================
// IMAGE TOOLS STUDIO ENGINE
// ============================================================================
let activeImageTool = "compress";
let stagedImageFile = null;

function openImageTool(op, title, desc) {
  activeImageTool = op;
  const drawer = document.getElementById("image-config-drawer");
  const drawerTitle = document.getElementById("img-drawer-title");
  const drawerDesc = document.getElementById("img-drawer-desc");
  const submitText = document.getElementById("img-submit-text");

  if (drawerTitle) drawerTitle.innerText = title;
  if (drawerDesc) drawerDesc.innerText = desc;
  if (submitText) submitText.innerText = `Process: ${title}`;

  renderImageToolControls(op);

  if (drawer) {
    drawer.style.display = "block";
    drawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  lucide.createIcons();
}

function closeImageDrawer() {
  const drawer = document.getElementById("image-config-drawer");
  if (drawer) drawer.style.display = "none";
}

function renderImageToolControls(op) {
  const container = document.getElementById("img-controls-container");
  if (!container) return;
  container.innerHTML = "";

  if (op === "compress") {
    container.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <label class="control-label" style="margin: 0;">COMPRESSION LEVEL &amp; QUALITY</label>
          <strong id="img-quality-label" style="font-family: 'Martian Mono', monospace; font-size: 0.85rem; color: var(--terracotta, #ea580c);">75% (Recommended)</strong>
        </div>
        <input type="range" id="img-quality-slider" min="15" max="98" value="75" class="broadsheet-range" style="width: 100%; accent-color: var(--terracotta, #ea580c);" oninput="document.getElementById('img-quality-label').innerText = this.value + '%' + (this.value > 85 ? ' (Near Lossless)' : this.value > 60 ? ' (Balanced)' : ' (Maximum Reduction)')">
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div>
          <label class="control-label" for="img-compress-target-fmt">OUTPUT ENCODING</label>
          <select id="img-compress-target-fmt" class="broadsheet-select">
            <option value="keep" selected>Preserve Original Format</option>
            <option value="webp">Next-Gen WebP (Up to 40% smaller)</option>
            <option value="jpg">Standard JPEG</option>
            <option value="png">Lossless PNG</option>
          </select>
        </div>
        <div>
          <label class="control-label" for="img-compress-preset">PRESET PROFILE</label>
          <select id="img-compress-preset" class="broadsheet-select" onchange="document.getElementById('img-quality-slider').value = this.value; document.getElementById('img-quality-slider').dispatchEvent(new Event('input'))">
            <option value="75" selected>Web &amp; Mobile Standard (75%)</option>
            <option value="90">High Print Fidelity (90%)</option>
            <option value="50">Ultra Web Delivery (50%)</option>
            <option value="30">Aggressive Email Attachment (30%)</option>
          </select>
        </div>
      </div>
    `;
  } else if (op === "resize") {
    container.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div>
          <label class="control-label" for="img-resize-width">TARGET WIDTH (PX)</label>
          <input type="number" id="img-resize-width" class="broadsheet-input" placeholder="e.g. 1920" min="10" max="10000">
        </div>
        <div>
          <label class="control-label" for="img-resize-height">TARGET HEIGHT (PX)</label>
          <input type="number" id="img-resize-height" class="broadsheet-input" placeholder="e.g. 1080" min="10" max="10000">
        </div>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div>
          <label class="control-label" for="img-resize-mode">PERCENTAGE SCALE</label>
          <select id="img-resize-mode" class="broadsheet-select" onchange="if (this.value) { document.getElementById('img-resize-width').value = ''; document.getElementById('img-resize-height').value = ''; }">
            <option value="" selected>Custom Pixel Dimensions</option>
            <option value="75">75% of Original</option>
            <option value="50">50% Half Size</option>
            <option value="25">25% Quarter Size</option>
          </select>
        </div>
        <div>
          <label class="control-label" for="img-resize-filter">RESAMPLING ALGORITHM</label>
          <select id="img-resize-filter" class="broadsheet-select">
            <option value="lanczos" selected>Lanczos (Sharpest &amp; Highest Quality)</option>
            <option value="bicubic">Bicubic (Smooth Interpolation)</option>
            <option value="bilinear">Bilinear (Fast Standard)</option>
          </select>
        </div>
      </div>
    `;
  } else if (op === "crop") {
    container.innerHTML = `
      <div>
        <label class="control-label" for="img-crop-ratio">ASPECT RATIO / STANDARD</label>
        <select id="img-crop-ratio" class="broadsheet-select" onchange="document.getElementById('custom-crop-coords').style.display = (this.value === 'custom' ? 'grid' : 'none')">
          <option value="1:1" selected>1:1 Square (Profile / Social / Icon)</option>
          <option value="16:9">16:9 Landscape (HD Video / Hero Banner)</option>
          <option value="9:16">9:16 Vertical (Stories / TikTok / Reels)</option>
          <option value="4:3">4:3 Standard Digital Photo</option>
          <option value="3:2">3:2 Classic 35mm DSLR</option>
          <option value="custom">Manual Pixel Coordinates (X, Y, W, H)</option>
        </select>
      </div>
      <div id="custom-crop-coords" style="display: none; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-top: 0.5rem;">
        <div><label class="control-label" style="font-size: 0.68rem;">LEFT (X)</label><input type="number" id="crop-left" class="broadsheet-input" value="0"></div>
        <div><label class="control-label" style="font-size: 0.68rem;">TOP (Y)</label><input type="number" id="crop-top" class="broadsheet-input" value="0"></div>
        <div><label class="control-label" style="font-size: 0.68rem;">WIDTH</label><input type="number" id="crop-w" class="broadsheet-input" placeholder="Auto"></div>
        <div><label class="control-label" style="font-size: 0.68rem;">HEIGHT</label><input type="number" id="crop-h" class="broadsheet-input" placeholder="Auto"></div>
      </div>
    `;
  } else if (op === "photo-editor") {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
        <label class="control-label" style="margin: 0;">ADJUSTMENT CONTROLS</label>
        <button type="button" class="ai-magic-btn" onclick="runAiImageVisionAssist('photo-enhance')">
          <i data-lucide="sparkles" style="width: 12px; height: 12px;"></i>
          <span>✨ AI Auto-Enhance (GPT-4o-mini)</span>
        </button>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div>
          <div style="display: flex; justify-content: space-between;"><label class="control-label">BRIGHTNESS</label><span id="val-bright" style="font-size: 0.75rem; color: var(--text-muted);">1.0</span></div>
          <input type="range" id="img-brightness" min="0.5" max="1.8" step="0.05" value="1.0" class="broadsheet-range" style="width: 100%; accent-color: var(--terracotta, #ea580c);" oninput="document.getElementById('val-bright').innerText = this.value">
        </div>
        <div>
          <div style="display: flex; justify-content: space-between;"><label class="control-label">CONTRAST</label><span id="val-contrast" style="font-size: 0.75rem; color: var(--text-muted);">1.0</span></div>
          <input type="range" id="img-contrast" min="0.5" max="1.8" step="0.05" value="1.0" class="broadsheet-range" style="width: 100%; accent-color: var(--terracotta, #ea580c);" oninput="document.getElementById('val-contrast').innerText = this.value">
        </div>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
        <div>
          <div style="display: flex; justify-content: space-between;"><label class="control-label">SATURATION / VIBRANCE</label><span id="val-sat" style="font-size: 0.75rem; color: var(--text-muted);">1.0</span></div>
          <input type="range" id="img-saturation" min="0.0" max="2.0" step="0.05" value="1.0" class="broadsheet-range" style="width: 100%; accent-color: var(--terracotta, #ea580c);" oninput="document.getElementById('val-sat').innerText = this.value">
        </div>
        <div>
          <div style="display: flex; justify-content: space-between;"><label class="control-label">SHARPNESS</label><span id="val-sharp" style="font-size: 0.75rem; color: var(--text-muted);">1.0</span></div>
          <input type="range" id="img-sharpness" min="0.5" max="2.5" step="0.1" value="1.0" class="broadsheet-range" style="width: 100%; accent-color: var(--terracotta, #ea580c);" oninput="document.getElementById('val-sharp').innerText = this.value">
        </div>
      </div>
      <div style="margin-top: 0.5rem;">
        <label class="control-label" for="img-filter-select">CREATIVE COLOR GRADE &amp; LUT</label>
        <select id="img-filter-select" class="broadsheet-select">
          <option value="" selected>Normal (Preserve Original Colors)</option>
          <option value="vintage">Vintage Kodachrome 1970s</option>
          <option value="sepia">Warm Architectural Sepia</option>
          <option value="grayscale">High-Contrast Fine Art Monochrome</option>
          <option value="invert">Negative Inverted Solarize</option>
        </select>
      </div>
    `;
  } else if (op === "upscale") {
    container.innerHTML = `
      <div>
        <label class="control-label" for="img-upscale-factor">SUPER-RESOLUTION FACTOR</label>
        <select id="img-upscale-factor" class="broadsheet-select">
          <option value="2" selected>2x Resolution (Lanczos Supersampling + Unsharp Mask)</option>
          <option value="4">4x Ultra HD (Architectural &amp; Blueprint Detail Enhancement)</option>
        </select>
      </div>
      <div style="padding: 10px 12px; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 6px; font-size: 0.78rem; color: var(--text-ink); margin-top: 0.5rem;">
        🔬 <strong>Zero Blur Guarantee:</strong> Multi-pass high-frequency sharpening restores crisp edges on line drawings, vector rasterizations, and technical diagrams.
      </div>
    `;
  } else if (op === "remove-background") {
    container.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div>
          <label class="control-label" for="img-nobg-tolerance">DETECTION SENSITIVITY</label>
          <select id="img-nobg-tolerance" class="broadsheet-select">
            <option value="20">Strict (Fine Subject Contours)</option>
            <option value="35" selected>Balanced Standard (35)</option>
            <option value="55">Aggressive Cutout (55)</option>
          </select>
        </div>
        <div>
          <label class="control-label" for="img-nobg-feather">EDGE FEATHERING</label>
          <select id="img-nobg-feather" class="broadsheet-select">
            <option value="smooth" selected>Soft Alpha Feathering (Anti-Aliased)</option>
            <option value="sharp">Hard Pixel Boundary</option>
          </select>
        </div>
      </div>
      <div style="padding: 10px 12px; background: var(--bg-stone-subtle); border-radius: 6px; font-size: 0.78rem; color: var(--text-muted); margin-top: 0.5rem;">
        ✨ Isolates foreground subject and generates transparent 32-bit RGBA PNG with alpha channel.
      </div>
    `;
  } else if (op === "watermark") {
    container.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
          <label class="control-label" for="img-watermark-text" style="margin: 0;">WATERMARK TEXT &amp; PRESETS</label>
          <div style="display: flex; gap: 6px;">
            <button type="button" class="ai-magic-btn" onclick="runAiImageVisionAssist('watermark')">
              <i data-lucide="sparkles" style="width: 12px; height: 12px;"></i>
              <span>✨ AI Vision Watermark</span>
            </button>
            <button type="button" class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.72rem; gap: 4px;" onclick="suggestAiWatermark()">
              <i data-lucide="list" style="width: 12px; height: 12px;"></i>
              <span>Presets</span>
            </button>
          </div>
        </div>
        <input type="text" id="img-watermark-text" class="broadsheet-input" value="CONFIDENTIAL" placeholder="e.g. CONFIDENTIAL, PREVIEW, COPYRIGHT 2026" oninput="updateInteractiveCanvasBadge()" style="margin-top: 4px;">
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.75rem; margin-top: 0.5rem;">
        <div>
          <label class="control-label" for="img-wm-position">PLACEMENT PRESET</label>
          <select id="img-wm-position" class="broadsheet-select" onchange="syncPresetToCanvas(this.value)">
            <option value="center" selected>Center (Default)</option>
            <option value="bottom-right">Bottom-Right Corner</option>
            <option value="bottom-left">Bottom-Left Corner</option>
            <option value="top-right">Top-Right Corner</option>
            <option value="top-left">Top-Left Corner</option>
            <option value="custom">Custom Drag Position</option>
          </select>
        </div>
        <div>
          <label class="control-label" for="img-wm-angle">ROTATION ANGLE</label>
          <select id="img-wm-angle" class="broadsheet-select" onchange="updateInteractiveCanvasBadge()">
            <option value="0" selected>0° Horizontal</option>
            <option value="45">45° Diagonal</option>
            <option value="-45">-45° Reverse Diagonal</option>
            <option value="90">90° Vertical</option>
          </select>
        </div>
        <div>
          <label class="control-label" for="img-wm-opacity">OPACITY</label>
          <select id="img-wm-opacity" class="broadsheet-select" onchange="updateInteractiveCanvasBadge()">
            <option value="0.2">20% Subtle</option>
            <option value="0.4" selected>40% Balanced</option>
            <option value="0.7">70% Prominent</option>
            <option value="1.0">100% Solid</option>
          </select>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.5rem;">
        <div>
          <label class="control-label" for="img-wm-color">TEXT COLOR</label>
          <select id="img-wm-color" class="broadsheet-select" onchange="updateInteractiveCanvasBadge()">
            <option value="#ffffff" selected>White (#FFFFFF)</option>
            <option value="#ea580c">Terracotta Orange (#EA580C)</option>
            <option value="#0f172a">Deep Charcoal (#0F172A)</option>
            <option value="#dc2626">Security Red (#DC2626)</option>
          </select>
        </div>
        <div>
          <label class="control-label" for="img-wm-tile">REPETITION PATTERN</label>
          <select id="img-wm-tile" class="broadsheet-select">
            <option value="single" selected>Single Watermark Stamp</option>
            <option value="tile">Repeating Grid Matrix (Tiled)</option>
          </select>
        </div>
      </div>
    `;
  } else if (op === "sign") {
    container.innerHTML = `
      <!-- Signature Mode: Simple Handwriting vs Digital Seal -->
      <div style="margin-bottom: 0.75rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <label class="control-label" style="margin-bottom: 0;">SIGNATURE TYPE</label>
          <button type="button" class="ai-magic-btn" onclick="runAiImageVisionAssist('sign')">
            <i data-lucide="sparkles" style="width: 12px; height: 12px;"></i>
            <span>✨ AI Auto-Signer &amp; Place</span>
          </button>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
          <button type="button" id="img-sign-type-simple" class="sign-type-btn active" onclick="selectImageSignType('simple')" style="border: 2px solid #ea580c; background: rgba(234, 88, 12, 0.04); border-radius: 8px; padding: 0.75rem; text-align: center; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 6px; transition: all 150ms ease;">
            <i data-lucide="pen-tool" style="width: 20px; height: 20px; color: #ea580c;"></i>
            <strong style="font-size: 0.85rem; color: var(--text-ink);">Simple Signature</strong>
            <span style="font-size: 0.7rem; color: var(--text-muted);">Cursive calligraphy</span>
          </button>
          <button type="button" id="img-sign-type-digital" class="sign-type-btn" onclick="selectImageSignType('digital')" style="border: 1px solid var(--border-ash); background: var(--bg-paper); border-radius: 8px; padding: 0.75rem; text-align: center; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 6px; transition: all 150ms ease;">
            <i data-lucide="award" style="width: 20px; height: 20px; color: #2563eb;"></i>
            <div style="display: inline-flex; align-items: center; gap: 4px;">
              <strong style="font-size: 0.85rem; color: var(--text-ink);">Digital Seal Badge</strong>
              <span class="badge" style="background: rgba(234, 179, 8, 0.15); color: #b45309; font-size: 0.65rem; padding: 1px 5px;">PRO</span>
            </div>
            <span style="font-size: 0.7rem; color: var(--text-muted);">Cryptographic stamp</span>
          </button>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div>
          <label class="control-label" for="img-sign-name-input">SIGNER NAME</label>
          <input type="text" id="img-sign-name-input" class="broadsheet-input" value="Musthaque Ali" oninput="updateInteractiveCanvasBadge()">
        </div>
        <div>
          <label class="control-label" for="img-sign-initials-input">INITIALS</label>
          <input type="text" id="img-sign-initials-input" class="broadsheet-input" value="MA" maxlength="4" placeholder="e.g. MA" oninput="updateInteractiveCanvasBadge()">
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.5rem;">
        <div>
          <label class="control-label" for="img-sign-placement-pos">STAMP PLACEMENT</label>
          <select id="img-sign-placement-pos" class="broadsheet-select" onchange="syncPresetToCanvas(this.value)">
            <option value="bottom-right" selected>Bottom-Right Corner</option>
            <option value="bottom-left">Bottom-Left Corner</option>
            <option value="top-right">Top-Right Corner</option>
            <option value="top-left">Top-Left Corner</option>
            <option value="custom">Custom Drag Position</option>
          </select>
        </div>
        <div>
          <label class="control-label" for="img-sign-reason-input">REASON / TITLE</label>
          <input type="text" id="img-sign-reason-input" class="broadsheet-input" value="Approved & Verified" placeholder="Approved & Verified" oninput="updateInteractiveCanvasBadge()">
        </div>
      </div>
    `;
  } else if (op === "meme-generator") {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <label class="control-label" style="margin: 0;">MEME CAPTIONS</label>
        <button type="button" class="ai-magic-btn" onclick="runAiImageVisionAssist('meme')">
          <i data-lucide="sparkles" style="width: 12px; height: 12px;"></i>
          <span>✨ AI Meme Generator (GPT-4o-mini)</span>
        </button>
      </div>
      <div>
        <label class="control-label" for="meme-top-text">TOP HEADER CAPTION</label>
        <input type="text" id="meme-top-text" class="broadsheet-input" placeholder="ONE DOES NOT SIMPLY" style="width: 100%;">
      </div>
      <div style="margin-top: 0.5rem;">
        <label class="control-label" for="meme-bottom-text">BOTTOM FOOTER CAPTION</label>
        <input type="text" id="meme-bottom-text" class="broadsheet-input" placeholder="CONVERT CAD WITH ZERO CLOUD EGRESS" style="width: 100%;">
      </div>
    `;
  } else if (op === "blur-face") {
    container.innerHTML = `
      <div>
        <div style="display: flex; justify-content: space-between;"><label class="control-label">BLUR PRIVACY INTENSITY</label><strong id="img-blur-label" style="font-family: 'Martian Mono', monospace; font-size: 0.85rem; color: var(--terracotta, #ea580c);">35px</strong></div>
        <input type="range" id="img-blur-strength" min="15" max="90" value="35" class="broadsheet-range" style="width: 100%; accent-color: var(--terracotta, #ea580c);" oninput="document.getElementById('img-blur-label').innerText = this.value + 'px'">
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">Automatic face-area oval detection with feathered Gaussian privacy shielding.</div>
      </div>
    `;
  } else if (op === "image-ocr") {
    container.innerHTML = `
      <div style="padding: 12px 14px; background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 8px; font-size: 0.82rem; color: var(--text-ink);">
        🔍 <strong>GPT-4o-mini Multimodal Vision OCR:</strong> Transcribes low-resolution scans, handwritten notes, invoices, blueprints, and whiteboard diagrams into structured GitHub-flavored Markdown.
      </div>
    `;
  } else if (op === "image-caption") {
    container.innerHTML = `
      <div style="padding: 12px 14px; background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 8px; font-size: 0.82rem; color: var(--text-ink);">
        ✨ <strong>AI Alt-Text &amp; SEO Generator:</strong> Generates WCAG accessibility descriptions, detailed scene breakdowns, and keyword tags with one click.
      </div>
    `;
  } else if (op === "rotate") {
    container.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div>
          <label class="control-label" for="img-rotate-angle">ROTATION ANGLE</label>
          <select id="img-rotate-angle" class="broadsheet-select">
            <option value="90" selected>90° Clockwise</option>
            <option value="180">180° Half Turn</option>
            <option value="270">270° Counter-Clockwise</option>
          </select>
        </div>
        <div>
          <label class="control-label" for="img-flip-mode">GEOMETRIC MIRROR</label>
          <select id="img-flip-mode" class="broadsheet-select">
            <option value="none" selected>No Flip</option>
            <option value="horizontal">Flip Horizontal (Mirror X)</option>
            <option value="vertical">Flip Vertical (Mirror Y)</option>
            <option value="both">Flip Both Axes</option>
          </select>
        </div>
      </div>
    `;
  }
}

function handleImageToolFileSelect(files) {
  if (!files || !files.length) return;
  stagedImageFile = files[0];

  const nameEl = document.getElementById("img-staged-name");
  const sizeEl = document.getElementById("img-staged-size");
  const strip = document.getElementById("img-staged-info");
  const dropzone = document.getElementById("img-dropzone");
  const submitBtn = document.getElementById("img-submit-btn");

  if (nameEl) nameEl.innerText = stagedImageFile.name;
  if (sizeEl) sizeEl.innerText = formatBytes(stagedImageFile.size);
  if (strip) strip.style.display = "flex";
  if (dropzone) dropzone.style.display = "none";
  if (submitBtn) submitBtn.disabled = false;

  // Load and display live visual canvas stage
  setupInteractiveCanvasStage(stagedImageFile);

  updateCloudEgressMetric(0, 0);
  lucide.createIcons();
}

function clearImageStagedFile(e) {
  if (e) e.stopPropagation();
  stagedImageFile = null;
  customBadgeCoords = null;
  const strip = document.getElementById("img-staged-info");
  const dropzone = document.getElementById("img-dropzone");
  const submitBtn = document.getElementById("img-submit-btn");
  const input = document.getElementById("img-file-input");
  const stage = document.getElementById("img-interactive-stage-wrap");

  if (strip) strip.style.display = "none";
  if (dropzone) dropzone.style.display = "block";
  if (submitBtn) submitBtn.disabled = true;
  if (input) input.value = "";
  if (stage) stage.style.display = "none";
  document.getElementById("img-result-card").style.display = "none";
  document.getElementById("img-progress-wrap").style.display = "none";
}

async function executeImageTool() {
  if (!stagedImageFile) return;

  const btn = document.getElementById("img-submit-btn");
  const progWrap = document.getElementById("img-progress-wrap");
  const progBar = document.getElementById("img-progress-bar");
  const progText = document.getElementById("img-progress-text");
  const resCard = document.getElementById("img-result-card");

  btn.disabled = true;
  progWrap.style.display = "block";
  resCard.style.display = "none";
  progBar.style.width = "25%";
  progText.innerText = "Processing image...";

  const fd = new FormData();
  fd.append("file", stagedImageFile);

  const opts = {};
  if (activeImageTool === "compress") {
    opts.quality = parseInt(document.getElementById("img-quality-slider")?.value || "75", 10);
    opts.target_format = document.getElementById("img-compress-target-fmt")?.value || "keep";
  } else if (activeImageTool === "resize") {
    opts.width = parseInt(document.getElementById("img-resize-width")?.value || "0", 10);
    opts.height = parseInt(document.getElementById("img-resize-height")?.value || "0", 10);
    opts.scale_pct = parseInt(document.getElementById("img-resize-mode")?.value || "0", 10);
    opts.resample = document.getElementById("img-resize-filter")?.value || "lanczos";
  } else if (activeImageTool === "upscale") {
    opts.scale = parseInt(document.getElementById("img-upscale-factor")?.value || "2", 10);
  } else if (activeImageTool === "crop") {
    opts.aspect_ratio = document.getElementById("img-crop-ratio")?.value || "1:1";
    opts.left = parseInt(document.getElementById("crop-left")?.value || "0", 10);
    opts.top = parseInt(document.getElementById("crop-top")?.value || "0", 10);
    opts.width = parseInt(document.getElementById("crop-w")?.value || "0", 10) || null;
    opts.height = parseInt(document.getElementById("crop-h")?.value || "0", 10) || null;
  } else if (activeImageTool === "photo-editor") {
    opts.brightness = parseFloat(document.getElementById("img-brightness")?.value || "1.0");
    opts.contrast = parseFloat(document.getElementById("img-contrast")?.value || "1.0");
    opts.saturation = parseFloat(document.getElementById("img-saturation")?.value || "1.0");
    opts.sharpness = parseFloat(document.getElementById("img-sharpness")?.value || "1.0");
    opts.filter = document.getElementById("img-filter-select")?.value || "";
  } else if (activeImageTool === "meme-generator") {
    opts.top_text = document.getElementById("meme-top-text")?.value || "";
    opts.bottom_text = document.getElementById("meme-bottom-text")?.value || "";
  } else if (activeImageTool === "watermark") {
    opts.text = document.getElementById("img-watermark-text")?.value || "CONFIDENTIAL";
    opts.position = document.getElementById("img-wm-position")?.value || "center";
    opts.angle = parseFloat(document.getElementById("img-wm-angle")?.value || "0");
    opts.opacity = parseFloat(document.getElementById("img-wm-opacity")?.value || "0.4");
    opts.color = document.getElementById("img-wm-color")?.value || "#ffffff";
    opts.tile = (document.getElementById("img-wm-tile")?.value === "tile");
    if (opts.position === "custom" && customBadgeCoords) {
      opts.custom_x = customBadgeCoords.x;
      opts.custom_y = customBadgeCoords.y;
    }
  } else if (activeImageTool === "sign") {
    opts.signer = document.getElementById("img-sign-name-input")?.value || "Musthaque Ali";
    opts.initials = document.getElementById("img-sign-initials-input")?.value || "MA";
    opts.reason = document.getElementById("img-sign-reason-input")?.value || "Approved & Verified";
    opts.sig_type = activeImgSignType || "simple";
    opts.position = document.getElementById("img-sign-placement-pos")?.value || "bottom-right";
    if (opts.position === "custom" && customBadgeCoords) {
      opts.custom_x = customBadgeCoords.x;
      opts.custom_y = customBadgeCoords.y;
    }
  } else if (activeImageTool === "blur-face") {
    opts.blur_strength = parseInt(document.getElementById("img-blur-strength")?.value || "35", 10);
  } else if (activeImageTool === "remove-background") {
    opts.tolerance = parseInt(document.getElementById("img-nobg-tolerance")?.value || "35", 10);
  } else if (activeImageTool === "rotate") {
    opts.angle = parseInt(document.getElementById("img-rotate-angle")?.value || "90", 10);
    const flipMode = document.getElementById("img-flip-mode")?.value || "none";
    opts.flip_h = (flipMode === "horizontal" || flipMode === "both");
    opts.flip_v = (flipMode === "vertical" || flipMode === "both");
  }

  fd.append("options", JSON.stringify(opts));

  if (activeImageTool === "image-ocr" || activeImageTool === "image-caption") {
    // Route to AI endpoint
    try {
      progBar.style.width = "40%";
      progText.innerText = "Transmitting to OpenRouter GPT-4o-mini Vision...";
      const res = await fetch(`/api/ai/${activeImageTool}`, {
        method: "POST",
        body: fd
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "AI vision processing failed");

      progBar.style.width = "100%";
      setTimeout(() => {
        progWrap.style.display = "none";
        resCard.style.display = "block";
        document.getElementById("img-result-title").innerText = `Ready: ${data.output_filename}`;
        const outputText = data.meta?.markdown || data.meta?.alt_text || JSON.stringify(data.meta, null, 2);
        document.getElementById("img-result-meta").innerText = `${formatBytes(data.file_size)} • ${data.duration_ms}ms • GPT-4o-mini Vision`;
        const dl = document.getElementById("img-download-link");
        if (dl) {
          dl.href = data.download_url;
          dl.setAttribute("download", data.output_filename);
        }
        btn.disabled = false;
        alert("✨ AI Result:\n\n" + outputText);
      }, 400);
      return;
    } catch (err) {
      progWrap.style.display = "none";
      btn.disabled = false;
      alert("AI Processing Error: " + err.message);
      return;
    }
  }

  let apiOp = activeImageTool;
  if (activeImageTool === "to-jpg") apiOp = "compress";
  if (activeImageTool === "from-jpg") apiOp = "compress";

  try {
    progBar.style.width = "65%";
    const res = await fetch(`/api/image/${apiOp}`, {
      method: "POST",
      body: fd
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Image processing failed");

    progBar.style.width = "100%";
    setTimeout(() => {
      progWrap.style.display = "none";
      resCard.style.display = "block";
      document.getElementById("img-result-title").innerText = `Ready: ${data.output_filename}`;
      document.getElementById("img-result-meta").innerText = `${formatBytes(data.file_size)} • ${data.duration_ms}ms • Local Zero Egress`;
      const dl = document.getElementById("img-download-link");
      if (dl) {
        dl.href = data.download_url;
        dl.setAttribute("download", data.output_filename);
      }
      updateCloudEgressMetric(data.file_size || 0, 1);
      btn.disabled = false;
      lucide.createIcons();
    }, 400);

  } catch (err) {
    progWrap.style.display = "none";
    btn.disabled = false;
    alert("Error: " + err.message);
  }
}


// ============================================================================
// PDF INTELLIGENCE (AI) STUDIO ENGINE (OPENROUTER POWERED)
// ============================================================================
let activeAiTool = "summarize";
let stagedAiFile = null;
let lastAiMarkdownContent = "";

function selectAiWorkspaceTool(tool) {
  activeAiTool = tool;
  const titleMap = {
    'summarize': 'AI Document Summarizer',
    'translate': 'AI Multilingual Document Translator',
    'markdown': 'PDF to Publication-Ready Markdown',
    'ocr': 'AI Multimodal OCR & Vision',
    'contract-audit': 'Contract & Legal Risk Auditor',
    'cad-titleblock-inspect': 'CAD Sheet Title Block Inspector & Renamer'
  };
  const descMap = {
    'summarize': 'Generates high-impact executive summaries, strategic takeaways, key metrics, and recommended next steps.',
    'translate': 'Translates documents into 10+ languages preserving layout, tables, and context.',
    'markdown': 'Converts complex PDFs into clean GitHub-flavored Markdown ready for documentation or publishing.',
    'ocr': 'Accurately transcribes low-resolution scans, invoices, and blueprints into editable digital text.',
    'contract-audit': 'Scans agreements and contracts to detect liability exposure, termination traps, and auto-renewals.',
    'cad-titleblock-inspect': 'Inspects drawings to extract Sheet Number, Revision, and Discipline, automatically renaming PDFs to standard engineering formats.'
  };

  document.getElementById("ai-tool-header-title").innerText = titleMap[tool] || 'AI Document Intelligence';
  document.getElementById("ai-tool-header-desc").innerText = descMap[tool] || '';

  const modeWrap = document.getElementById("ai-mode-selector-wrap");
  const langWrap = document.getElementById("ai-language-selector-wrap");

  if (tool === 'summarize') {
    if (modeWrap) modeWrap.style.display = "block";
    if (langWrap) langWrap.style.display = "none";
  } else if (tool === 'translate') {
    if (modeWrap) modeWrap.style.display = "none";
    if (langWrap) langWrap.style.display = "block";
  } else {
    if (modeWrap) modeWrap.style.display = "none";
    if (langWrap) langWrap.style.display = "none";
  }

  const panel = document.getElementById("ai-workspace-panel");
  if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  lucide.createIcons();
}

function handleAiFileSelect(files) {
  if (!files || !files.length) return;
  stagedAiFile = files[0];

  const nameEl = document.getElementById("ai-staged-name");
  const sizeEl = document.getElementById("ai-staged-size");
  const strip = document.getElementById("ai-staged-info");
  const dropzone = document.getElementById("ai-dropzone");
  const submitBtn = document.getElementById("ai-submit-btn");

  if (nameEl) nameEl.innerText = stagedAiFile.name;
  if (sizeEl) sizeEl.innerText = formatBytes(stagedAiFile.size);
  if (strip) strip.style.display = "flex";
  if (dropzone) dropzone.style.display = "none";
  if (submitBtn) submitBtn.disabled = false;

  updateCloudEgressMetric(0, 0);
  lucide.createIcons();
}

function clearAiStagedFile(e) {
  if (e) e.stopPropagation();
  stagedAiFile = null;
  const strip = document.getElementById("ai-staged-info");
  const dropzone = document.getElementById("ai-dropzone");
  const submitBtn = document.getElementById("ai-submit-btn");
  const input = document.getElementById("ai-file-input");

  if (strip) strip.style.display = "none";
  if (dropzone) dropzone.style.display = "block";
  if (submitBtn) submitBtn.disabled = true;
  if (input) input.value = "";
  document.getElementById("ai-result-card").style.display = "none";
  document.getElementById("ai-progress-wrap").style.display = "none";
}

async function executeAiOperation() {
  if (!stagedAiFile) return;

  const btn = document.getElementById("ai-submit-btn");
  const progWrap = document.getElementById("ai-progress-wrap");
  const progBar = document.getElementById("ai-progress-bar");
  const progText = document.getElementById("ai-progress-text");
  const resCard = document.getElementById("ai-result-card");
  const outputEl = document.getElementById("ai-output-text-content");

  btn.disabled = true;
  progWrap.style.display = "block";
  resCard.style.display = "none";
  progBar.style.width = "30%";
  progText.innerText = "Extracting text and transmitting to OpenRouter GPT-4o-mini...";

  const fd = new FormData();
  fd.append("file", stagedAiFile);

  const opts = {};
  if (activeAiTool === "summarize") {
    opts.mode = document.getElementById("ai-summary-mode")?.value || "executive";
  } else if (activeAiTool === "translate") {
    opts.language = document.getElementById("ai-target-language")?.value || "Spanish";
  }

  fd.append("options", JSON.stringify(opts));

  try {
    progBar.style.width = "65%";
    progText.innerText = "Synthesizing intelligence response...";

    const res = await fetch(`/api/ai/${activeAiTool}`, {
      method: "POST",
      body: fd
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "AI execution failed");

    progBar.style.width = "100%";
    setTimeout(() => {
      progWrap.style.display = "none";
      resCard.style.display = "block";

      let rawContent = data.meta?.markdown || data.meta?.content || data.meta?.text || "";

      if (activeAiTool === "contract-audit" && data.meta?.clauses) {
        const score = data.meta.risk_score || "MEDIUM";
        const scoreColor = score === "HIGH" ? "#dc2626" : score === "MEDIUM" ? "#d97706" : "#16a34a";
        rawContent = `## ⚖️ Legal Risk Audit Scorecard\n\n` +
          `**Overall Agreement Risk Level:** <span style="display: inline-block; padding: 2px 8px; border-radius: 4px; background: ${scoreColor}22; color: ${scoreColor}; font-weight: 700;">${score} RISK</span>\n\n` +
          `### Executive Assessment\n${data.meta.executive_summary || ""}\n\n` +
          `### Flagged Contract Clauses\n` +
          data.meta.clauses.map(c => `
#### ${c.name} (${c.level} Risk)
> "${c.quote || ""}"
- **Legal Risk Analysis:** ${c.explanation}
- **💡 Recommended Counter-Proposal:** ${c.recommendation}
`).join("\n");
      }

      if (activeAiTool === "cad-titleblock-inspect" && data.meta?.sheet_number) {
        rawContent = `## 📐 CAD Drawing Title Block Metadata\n\n` +
          `| Parameter | Extracted Value |\n` +
          `| :--- | :--- |\n` +
          `| **Sheet Number** | \`${data.meta.sheet_number}\` |\n` +
          `| **Revision** | \`${data.meta.revision}\` |\n` +
          `| **Discipline** | **${data.meta.discipline}** |\n` +
          `| **Sheet Title** | ${data.meta.sheet_title} |\n` +
          `| **Project Name** | ${data.meta.project_name} |\n` +
          `| **Recommended Filename** | \`${data.meta.suggested_filename}\` |\n\n` +
          `*100% Native AutoCAD Compatibility Guarantee: Core plot configuration remains completely untouched.*`;
      }
      // Strip any lingering code fences
      const cleanContent = rawContent.replace(/^```(?:markdown|md)?\s*\n?/i, "").replace(/\n?```\s*$/i, "").trim();
      lastAiMarkdownContent = cleanContent;

      const formattedEl = document.getElementById("ai-output-formatted");
      const rawEl = document.getElementById("ai-output-raw");
      const legacyEl = document.getElementById("ai-output-text-content");

      if (formattedEl) formattedEl.innerHTML = renderMarkdownToHtml(cleanContent);
      if (rawEl) rawEl.innerText = cleanContent;
      if (legacyEl) legacyEl.innerText = cleanContent;

      // Reset to formatted view by default
      switchAiOutputView("formatted");

      const dl = document.getElementById("ai-download-btn");
      if (dl) {
        dl.href = data.download_url;
        dl.setAttribute("download", data.output_filename);
      }

      updateCloudEgressMetric(data.file_size || 0, 1);
      btn.disabled = false;
      lucide.createIcons();
    }, 400);

  } catch (err) {
    progWrap.style.display = "none";
    btn.disabled = false;
    alert("AI Error: " + err.message);
  }
}

function switchAiOutputView(view) {
  const formattedEl = document.getElementById("ai-output-formatted");
  const rawEl = document.getElementById("ai-output-raw");
  const btnFormatted = document.getElementById("ai-view-btn-formatted");
  const btnRaw = document.getElementById("ai-view-btn-raw");

  if (view === "raw") {
    if (formattedEl) formattedEl.style.display = "none";
    if (rawEl) rawEl.style.display = "block";
    if (btnRaw) {
      btnRaw.style.background = "#ffffff";
      btnRaw.style.color = "var(--text-ink, #0f172a)";
      btnRaw.style.boxShadow = "0 1px 2px rgba(0,0,0,0.06)";
    }
    if (btnFormatted) {
      btnFormatted.style.background = "transparent";
      btnFormatted.style.color = "var(--text-muted, #64748b)";
      btnFormatted.style.boxShadow = "none";
    }
  } else {
    if (formattedEl) formattedEl.style.display = "block";
    if (rawEl) rawEl.style.display = "none";
    if (btnFormatted) {
      btnFormatted.style.background = "#ffffff";
      btnFormatted.style.color = "var(--text-ink, #0f172a)";
      btnFormatted.style.boxShadow = "0 1px 2px rgba(0,0,0,0.06)";
    }
    if (btnRaw) {
      btnRaw.style.background = "transparent";
      btnRaw.style.color = "var(--text-muted, #64748b)";
      btnRaw.style.boxShadow = "none";
    }
  }
}

function copyAiResultToClipboard() {
  if (!lastAiMarkdownContent) return;
  navigator.clipboard.writeText(lastAiMarkdownContent).then(() => {
    const btnText = document.getElementById("ai-copy-btn-text");
    if (btnText) {
      btnText.innerText = "Copied!";
      setTimeout(() => { btnText.innerText = "Copy"; }, 2000);
    }
  });
}

/**
 * Universal Zero-Dependency Markdown-to-HTML Parser
 * Parses headers, bold, italics, tables, lists, blockquotes, code blocks, horizontal rules
 */
function renderMarkdownToHtml(md) {
  if (!md) return "";
  
  // Clean outer fences if present
  let text = md.replace(/^```(?:markdown|md)?\s*\n?/i, "").replace(/\n?```\s*$/i, "").trim();

  // Escape HTML entities safely
  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Handle fenced code blocks
  const codeBlocks = [];
  text = text.replace(/```([a-z]*)\n([\s\S]*?)```/gi, (match, lang, code) => {
    const idx = codeBlocks.length;
    codeBlocks.push(`<pre class="ai-code-block"><code>${escapeHtml(code.trim())}</code></pre>`);
    return `@@CODEBLOCK_${idx}@@`;
  });

  const lines = text.split(/\r?\n/);
  const out = [];
  let inList = false;
  let listType = "ul";
  let inTable = false;
  let tableRows = [];

  function flushList() {
    if (inList) {
      out.push(`</${listType}>`);
      inList = false;
    }
  }

  function flushTable() {
    if (inTable) {
      if (tableRows.length > 0) {
        let tHtml = '<div class="ai-table-wrapper"><table class="ai-report-table">';
        tableRows.forEach((row, rIdx) => {
          const isHeader = (rIdx === 0);
          const tag = isHeader ? "th" : "td";
          tHtml += "<tr>";
          row.forEach(cell => {
            tHtml += `<${tag}>${inlineFormat(cell.trim())}</${tag}>`;
          });
          tHtml += "</tr>";
        });
        tHtml += '</table></div>';
        out.push(tHtml);
      }
      tableRows = [];
      inTable = false;
    }
  }

  function inlineFormat(str) {
    return str
      // inline code
      .replace(/`([^`]+)`/g, '<code class="ai-inline-code">$1</code>')
      // bold
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      // italic
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      // links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: var(--terracotta, #ea580c); text-decoration: underline;">$1</a>');
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Empty line
    if (!line) {
      flushList();
      flushTable();
      continue;
    }

    // Horizontal Rule
    if (/^(?:---|\*\*\*|___)$/.test(line)) {
      flushList();
      flushTable();
      out.push('<hr style="border: none; border-top: 1px solid var(--border-ash, #e2e8f0); margin: 1.5rem 0;">');
      continue;
    }

    // Markdown Table Detection
    if (line.startsWith("|") && line.endsWith("|")) {
      flushList();
      // Skip separator rows like |---|---|
      if (/^\|(?:\s*:?-+:?\s*\|)+$/.test(line)) {
        continue;
      }
      const cells = line.slice(1, -1).split("|");
      tableRows.push(cells);
      inTable = true;
      continue;
    } else {
      flushTable();
    }

    // Headings
    if (line.startsWith("# ")) {
      flushList();
      out.push(`<h1 class="ai-report-h1"><span class="material-symbols-outlined" style="font-size: 24px; color: var(--terracotta, #ea580c);">analytics</span> ${inlineFormat(line.substring(2))}</h1>`);
      continue;
    }
    if (line.startsWith("## ")) {
      flushList();
      out.push(`<h2 class="ai-report-h2">${inlineFormat(line.substring(3))}</h2>`);
      continue;
    }
    if (line.startsWith("### ")) {
      flushList();
      out.push(`<h3 class="ai-report-h3">${inlineFormat(line.substring(4))}</h3>`);
      continue;
    }
    if (line.startsWith("#### ")) {
      flushList();
      out.push(`<h4 style="font-size: 0.95rem; font-weight: 600; margin-top: 0.8rem; margin-bottom: 0.3rem;">${inlineFormat(line.substring(5))}</h4>`);
      continue;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      flushList();
      out.push(`<blockquote class="ai-report-blockquote">${inlineFormat(line.substring(2))}</blockquote>`);
      continue;
    }

    // Unordered List
    const bulletMatch = line.match(/^[-*•]\s+(.*)$/);
    if (bulletMatch) {
      if (!inList || listType !== "ul") {
        flushList();
        inList = true;
        listType = "ul";
        out.push('<ul class="ai-report-ul">');
      }
      out.push(`<li class="ai-report-li">${inlineFormat(bulletMatch[1])}</li>`);
      continue;
    }

    // Ordered List
    const numMatch = line.match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      if (!inList || listType !== "ol") {
        flushList();
        inList = true;
        listType = "ol";
        out.push('<ol class="ai-report-ol">');
      }
      out.push(`<li class="ai-report-li">${inlineFormat(numMatch[2])}</li>`);
      continue;
    }

    // Regular Paragraph
    flushList();
    out.push(`<p class="ai-report-p">${inlineFormat(line)}</p>`);
  }

  flushList();
  flushTable();

  let finalHtml = out.join("\n");

  // Restore code blocks
  codeBlocks.forEach((block, idx) => {
    finalHtml = finalHtml.replace(`@@CODEBLOCK_${idx}@@`, block);
  });

  return finalHtml;
}

// ---------------------------------------------------------------------------
// PDF Studio — Advanced Signature UI Helpers
// ---------------------------------------------------------------------------
let activeSignType = "simple";

function selectSignType(type) {
  activeSignType = type;
  const btnSimple = document.getElementById("sign-type-simple");
  const btnDigital = document.getElementById("sign-type-digital");

  if (btnSimple && btnDigital) {
    if (type === "simple") {
      btnSimple.style.border = "2px solid #ea580c";
      btnSimple.style.background = "rgba(234, 88, 12, 0.04)";
      btnDigital.style.border = "1px solid var(--border-ash)";
      btnDigital.style.background = "var(--bg-paper)";
    } else {
      btnDigital.style.border = "2px solid #2563eb";
      btnDigital.style.background = "rgba(37, 99, 235, 0.04)";
      btnSimple.style.border = "1px solid var(--border-ash)";
      btnSimple.style.background = "var(--bg-paper)";
    }
  }
}

function updateSignPreview(name) {
  const p = document.getElementById("sign-preview-text");
  if (p) {
    p.innerText = (name && name.trim()) ? name.trim() : "Musthaque Ali";
  }
}

// ---------------------------------------------------------------------------
// Image Studio — Interactive Visual Canvas & Drag-and-Drop Placement Studio
// ---------------------------------------------------------------------------
let activeImgSignType = "simple";
let customBadgeCoords = null; // { x: 0.0 - 1.0, y: 0.0 - 1.0 }

function selectImageSignType(type) {
  activeImgSignType = type;
  const btnSimple = document.getElementById("img-sign-type-simple");
  const btnDigital = document.getElementById("img-sign-type-digital");

  if (btnSimple && btnDigital) {
    if (type === "simple") {
      btnSimple.style.border = "2px solid #ea580c";
      btnSimple.style.background = "rgba(234, 88, 12, 0.04)";
      btnDigital.style.border = "1px solid var(--border-ash)";
      btnDigital.style.background = "var(--bg-paper)";
    } else {
      btnDigital.style.border = "2px solid #2563eb";
      btnDigital.style.background = "rgba(37, 99, 235, 0.04)";
      btnSimple.style.border = "1px solid var(--border-ash)";
      btnSimple.style.background = "var(--bg-paper)";
    }
  }
  updateInteractiveCanvasBadge();
}

function setupInteractiveCanvasStage(file) {
  const stage = document.getElementById("img-interactive-stage-wrap");
  const imgEl = document.getElementById("img-canvas-preview");
  const badge = document.getElementById("img-draggable-badge");
  if (!stage || !imgEl || !badge) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    imgEl.src = e.target.result;
    stage.style.display = "flex";
    badge.style.display = (activeImageTool === "watermark" || activeImageTool === "sign") ? "block" : "none";
    initBadgeDraggable();
    updateInteractiveCanvasBadge();
    lucide.createIcons();
  };
  reader.readAsDataURL(file);
}

function initBadgeDraggable() {
  const badge = document.getElementById("img-draggable-badge");
  const viewport = document.getElementById("img-canvas-viewport");
  if (!badge || !viewport || badge.dataset.dragInitialized) return;

  badge.dataset.dragInitialized = "true";
  let isDragging = false;
  let startX, startY, origLeft, origTop;

  function onPointerDown(e) {
    e.preventDefault();
    isDragging = true;
    const clientX = e.clientX || (e.touches && e.touches[0].clientX);
    const clientY = e.clientY || (e.touches && e.touches[0].clientY);
    startX = clientX;
    startY = clientY;

    const bRect = badge.getBoundingClientRect();
    const vRect = viewport.getBoundingClientRect();
    origLeft = bRect.left - vRect.left;
    origTop = bRect.top - vRect.top;

    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", onPointerUp);
    document.addEventListener("touchmove", onPointerMove, { passive: false });
    document.addEventListener("touchend", onPointerUp);
  }

  function onPointerMove(e) {
    if (!isDragging) return;
    if (e.cancelable) e.preventDefault();
    const clientX = e.clientX || (e.touches && e.touches[0].clientX);
    const clientY = e.clientY || (e.touches && e.touches[0].clientY);

    const dx = clientX - startX;
    const dy = clientY - startY;

    const vWidth = viewport.clientWidth;
    const vHeight = viewport.clientHeight;
    const bWidth = badge.offsetWidth;
    const bHeight = badge.offsetHeight;

    let newX = Math.max(0, Math.min(vWidth - bWidth, origLeft + dx));
    let newY = Math.max(0, Math.min(vHeight - bHeight, origTop + dy));

    badge.style.left = `${newX}px`;
    badge.style.top = `${newY}px`;

    // Save fractional relative coordinate
    customBadgeCoords = {
      x: Math.round((newX / vWidth) * 1000) / 1000,
      y: Math.round((newY / vHeight) * 1000) / 1000
    };

    // Update dropdown to 'custom'
    const posSel = (activeImageTool === "sign") 
      ? document.getElementById("img-sign-placement-pos") 
      : document.getElementById("img-wm-position");
    if (posSel) posSel.value = "custom";
  }

  function onPointerUp() {
    isDragging = false;
    document.removeEventListener("pointermove", onPointerMove);
    document.removeEventListener("pointerup", onPointerUp);
    document.removeEventListener("touchmove", onPointerMove);
    document.removeEventListener("touchend", onPointerUp);
  }

  badge.addEventListener("pointerdown", onPointerDown);
}

function updateInteractiveCanvasBadge() {
  const badge = document.getElementById("img-draggable-badge");
  const content = document.getElementById("img-badge-content");
  if (!badge || !content) return;

  if (activeImageTool === "sign") {
    badge.className = (activeImgSignType === "digital")
      ? "interactive-overlay-badge badge-signature-digital"
      : "interactive-overlay-badge badge-signature-simple";

    const name = document.getElementById("img-sign-name-input")?.value || "Musthaque Ali";
    const inits = document.getElementById("img-sign-initials-input")?.value || "MA";
    const reason = document.getElementById("img-sign-reason-input")?.value || "Approved & Verified";

    if (activeImgSignType === "digital") {
      badge.innerHTML = `
        <div style="font-size: 0.65rem; color: #2563eb; font-weight: 700; text-transform: uppercase;">✔ Digitally Verified</div>
        <div style="font-size: 0.88rem; font-weight: 700; color: #0f172a;">${escapeHtml(name)}</div>
        <div style="font-size: 0.65rem; color: #64748b;">Initials: [${escapeHtml(inits)}] • ${escapeHtml(reason)}</div>
      `;
    } else {
      badge.innerHTML = `
        <div style="font-size: 0.6rem; color: #94a3b8; text-transform: uppercase; font-family: -apple-system, sans-serif;">Signature</div>
        <div style="font-family: 'Dancing Script', 'Caveat', cursive; font-size: 1.35rem; color: #1e3a8a; font-weight: 700;">${escapeHtml(name)}</div>
      `;
    }
    badge.style.display = "block";

  } else if (activeImageTool === "watermark") {
    badge.className = "interactive-overlay-badge badge-watermark";
    const text = document.getElementById("img-watermark-text")?.value || "CONFIDENTIAL";
    const angle = document.getElementById("img-wm-angle")?.value || "0";
    const opacity = document.getElementById("img-wm-opacity")?.value || "0.4";
    const color = document.getElementById("img-wm-color")?.value || "#ffffff";

    badge.style.transform = `rotate(${angle}deg)`;
    badge.style.opacity = opacity;
    badge.style.color = color;
    badge.style.borderColor = color;
    badge.innerHTML = `<span style="text-shadow: 0 1px 3px rgba(0,0,0,0.6);">${escapeHtml(text)}</span>`;
    badge.style.display = "block";
  } else {
    badge.style.display = "none";
  }
}

function syncPresetToCanvas(pos) {
  const badge = document.getElementById("img-draggable-badge");
  const viewport = document.getElementById("img-canvas-viewport");
  if (!badge || !viewport || pos === "custom") return;

  const vWidth = viewport.clientWidth;
  const vHeight = viewport.clientHeight;
  const bWidth = badge.offsetWidth;
  const bHeight = badge.offsetHeight;

  let x = 20, y = 20;
  if (pos === "bottom-right") {
    x = vWidth - bWidth - 20;
    y = vHeight - bHeight - 20;
  } else if (pos === "bottom-left") {
    x = 20;
    y = vHeight - bHeight - 20;
  } else if (pos === "top-right") {
    x = vWidth - bWidth - 20;
    y = 20;
  } else if (pos === "top-left") {
    x = 20;
    y = 20;
  } else if (pos === "center") {
    x = Math.max(0, (vWidth - bWidth) / 2);
    y = Math.max(0, (vHeight - bHeight) / 2);
  }

  badge.style.left = `${x}px`;
  badge.style.top = `${y}px`;

  customBadgeCoords = {
    x: Math.round((x / vWidth) * 1000) / 1000,
    y: Math.round((y / vHeight) * 1000) / 1000
  };
}

// ---------------------------------------------------------------------------
// AI Document & Image Presets (Smart Automation)
// ---------------------------------------------------------------------------
function suggestAiWatermark() {
  const suggestions = [
    "CONFIDENTIAL // MUSTHAQUE ALI ARCHIVE",
    "VERIFIED & APPROVED FOR FABRICATION",
    "COPYRIGHT © 2026 — ALL RIGHTS RESERVED",
    "PRELIMINARY DESIGN — NOT FOR CONSTRUCTION",
    "DIGITALLY SIGNED & SEALED",
    "CLIENT REVIEW COPY // DO NOT DUPLICATE"
  ];
  const choice = suggestions[Math.floor(Math.random() * suggestions.length)];
  const input = document.getElementById("img-watermark-text");
  if (input) {
    input.value = choice;
    updateInteractiveCanvasBadge();
  }
}




// ===========================================================================
// CLAUDE-STYLE AI WORKSPACE & MULTIMODAL STUDIO CLIENT ENGINE (GPT-4o-mini)
// ===========================================================================

let claudeChats = [];
let activeClaudeChatId = null;
let stagedClaudeFile = null;
let activeClaudeArtifact = null;
let claudeSpeechRecognizer = null;

function loadClaudeChatsFromStorage() {
  try {
    const raw = localStorage.getItem("ilf_claude_chats");
    claudeChats = raw ? JSON.parse(raw) : [];
  } catch (e) {
    claudeChats = [];
  }
}

function saveClaudeChatsToStorage() {
  try {
    localStorage.setItem("ilf_claude_chats", JSON.stringify(claudeChats));
  } catch (e) {}
}

function initClaudeStudio() {
  loadClaudeChatsFromStorage();
  renderClaudeChatList();
  if (!activeClaudeChatId) {
    if (claudeChats.length > 0) {
      loadClaudeChat(claudeChats[0].id);
    } else {
      startNewClaudeChat();
    }
  }
}

function startNewClaudeChat() {
  activeClaudeChatId = "chat_" + Date.now();
  stagedClaudeFile = null;
  activeClaudeArtifact = null;

  const titleEl = document.getElementById("claude-active-chat-title");
  if (titleEl) titleEl.innerText = "New conversation";

  const hero = document.getElementById("claude-welcome-hero");
  if (hero) hero.style.display = "flex";

  const stream = document.getElementById("claude-message-stream");
  if (stream) {
    stream.innerHTML = "";
    stream.style.display = "none";
  }

  const input = document.getElementById("claude-prompt-input");
  if (input) {
    input.value = "";
    input.style.height = "auto";
    input.focus();
  }

  removeClaudeAttachment();
  closeClaudeArtifact();
  renderClaudeChatList();
}

function renderClaudeChatList() {
  const list = document.getElementById("claude-history-list");
  if (!list) return;

  if (claudeChats.length === 0) {
    list.innerHTML = `<div style="font-size: 0.75rem; color: #71717a; padding: 6px 10px;">No chats yet</div>`;
    return;
  }

  list.innerHTML = claudeChats.map(c => `
    <div class="claude-chat-item ${c.id === activeClaudeChatId ? 'active' : ''}" onclick="loadClaudeChat('${c.id}')">
      <i data-lucide="message-square" style="width: 14px; height: 14px; flex-shrink: 0; color: #71717a;"></i>
      <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(c.title || 'Untitled chat')}</span>
      <button type="button" class="claude-mini-btn" onclick="deleteClaudeChat('${c.id}', event)" title="Delete chat">
        <i data-lucide="x" style="width: 12px; height: 12px;"></i>
      </button>
    </div>
  `).join('');

  lucide.createIcons();
}

function loadClaudeChat(chatId) {
  activeClaudeChatId = chatId;
  const chat = claudeChats.find(c => c.id === chatId);
  if (!chat) return;

  const titleEl = document.getElementById("claude-active-chat-title");
  if (titleEl) titleEl.innerText = chat.title || "Conversation";

  const hero = document.getElementById("claude-welcome-hero");
  const stream = document.getElementById("claude-message-stream");

  if (!chat.messages || chat.messages.length === 0) {
    if (hero) hero.style.display = "flex";
    if (stream) stream.style.display = "none";
  } else {
    if (hero) hero.style.display = "none";
    if (stream) {
      stream.style.display = "flex";
      stream.innerHTML = "";
      chat.messages.forEach(msg => appendClaudeMessageBubble(msg.role, msg.content, msg.attachmentName, msg.artifact));
      stream.scrollTop = stream.scrollHeight;
    }
  }

  renderClaudeChatList();
}

function deleteClaudeChat(chatId, e) {
  if (e) e.stopPropagation();
  claudeChats = claudeChats.filter(c => c.id !== chatId);
  saveClaudeChatsToStorage();
  if (activeClaudeChatId === chatId) {
    if (claudeChats.length > 0) {
      loadClaudeChat(claudeChats[0].id);
    } else {
      startNewClaudeChat();
    }
  } else {
    renderClaudeChatList();
  }
}

function clearAllClaudeHistory() {
  if (confirm("Are you sure you want to clear all chat history?")) {
    claudeChats = [];
    saveClaudeChatsToStorage();
    startNewClaudeChat();
  }
}

function toggleClaudeSidebar() {
  const sb = document.getElementById("claude-sidebar");
  const openBtn = document.getElementById("claude-sidebar-open-btn");
  if (!sb) return;

  if (sb.classList.contains("collapsed")) {
    sb.classList.remove("collapsed");
    if (openBtn) openBtn.style.display = "none";
  } else {
    sb.classList.add("collapsed");
    if (openBtn) openBtn.style.display = "inline-flex";
  }
}

function switchClaudeViewMode(mode) {
  if (mode === "tools") {
    switchTab("ai");
  } else {
    switchTab("chat");
  }
}

function setClaudeSubmode(submode) {
  const btnChat = document.getElementById("claude-submode-chat");
  const btnCowork = document.getElementById("claude-submode-cowork");
  if (submode === "cowork") {
    if (btnCowork) btnCowork.classList.add("active");
    if (btnChat) btnChat.classList.remove("active");
  } else {
    if (btnChat) btnChat.classList.add("active");
    if (btnCowork) btnCowork.classList.remove("active");
  }
}

function handleClaudeFileAttach(files) {
  if (!files || !files.length) return;
  stagedClaudeFile = files[0];

  const chip = document.getElementById("claude-attachment-chip");
  const nameEl = document.getElementById("claude-attach-filename");
  const sizeEl = document.getElementById("claude-attach-size");

  if (chip && nameEl && sizeEl) {
    nameEl.innerText = stagedClaudeFile.name;
    sizeEl.innerText = formatBytes(stagedClaudeFile.size);
    chip.style.display = "inline-flex";
    lucide.createIcons();
  }
}

function removeClaudeAttachment() {
  stagedClaudeFile = null;
  const chip = document.getElementById("claude-attachment-chip");
  if (chip) chip.style.display = "none";
  const fileInput = document.getElementById("claude-file-input");
  if (fileInput) fileInput.value = "";
}

function autoExpandClaudeTextarea(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}

function handleClaudeTextareaKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendClaudeMessage();
  }
}

function triggerClaudeStarter(starterType) {
  const input = document.getElementById("claude-prompt-input");
  if (!input) return;
  if (starterType === "Summarize Document") {
    input.value = "Please analyze and summarize this attached document. Extract all key specifications, dates, scope, and critical takeaways.";
  } else if (starterType === "CAD Drawing Audit") {
    input.value = "Please perform a technical CAD audit on this drawing. Inspect layer configurations, title block details, line conventions, and drawing notes.";
  } else if (starterType === "Extract Tabular Data") {
    input.value = "Please extract all numerical tables, schedules, quantities, and column rows from this document into clean, formatted Markdown tables.";
  } else if (starterType === "Technical Q&A") {
    input.value = "What are the engineering standards and best practices for plotting AutoCAD DWG/DXF drawings with monochrome CTB pen tables?";
  }
  autoExpandClaudeTextarea(input);
  input.focus();
  if (stagedClaudeFile) {
    sendClaudeMessage();
  }
}

async function sendClaudeMessage() {
  const input = document.getElementById("claude-prompt-input");
  if (!input) return;
  let text = input.value.trim();
  if (!text && !stagedClaudeFile) {
    input.focus();
    return;
  }

  const attachedName = stagedClaudeFile ? stagedClaudeFile.name : null;
  const attachedFile = stagedClaudeFile;

  // If user only attached a file without entering a question, provide intelligent default
  if (!text && stagedClaudeFile) {
    text = `Please review and analyze this attached file '${attachedName}' thoroughly. Summarize all key technical details, specifications, tabular data, scope, or clauses, and provide clear takeaways.`;
  }

  const hero = document.getElementById("claude-welcome-hero");
  if (hero) hero.style.display = "none";

  const stream = document.getElementById("claude-message-stream");
  if (stream) stream.style.display = "flex";

  // Append user bubble
  appendClaudeMessageBubble("user", text, attachedName);

  // Clear input
  input.value = "";
  input.style.height = "auto";
  removeClaudeAttachment();

  // Find or create current chat
  let currentChat = claudeChats.find(c => c.id === activeClaudeChatId);
  if (!currentChat) {
    currentChat = {
      id: activeClaudeChatId || ("chat_" + Date.now()),
      title: text.slice(0, 32) || (attachedName ? `Analyze ${attachedName}` : "New conversation"),
      messages: [],
      timestamp: Date.now()
    };
    activeClaudeChatId = currentChat.id;
    claudeChats.unshift(currentChat);
  } else if (currentChat.messages.length === 0) {
    currentChat.title = text.slice(0, 32) || (attachedName ? `Analyze ${attachedName}` : "Conversation");
    const titleEl = document.getElementById("claude-active-chat-title");
    if (titleEl) titleEl.innerText = currentChat.title;
  }

  currentChat.messages.push({
    role: "user",
    content: text,
    attachmentName: attachedName
  });
  saveClaudeChatsToStorage();
  renderClaudeChatList();

  // Append thinking bubble
  const loadingId = "claude-loading-" + Date.now();
  const loadingDiv = document.createElement("div");
  loadingDiv.id = loadingId;
  loadingDiv.className = "claude-msg-assistant";
  loadingDiv.innerHTML = `
    <div style="display: inline-flex; align-items: center; gap: 8px; color: #818cf8; font-size: 0.85rem;">
      <i data-lucide="sparkles" class="spin" style="width: 14px; height: 14px;"></i>
      <span>Synthesizing intelligence with GPT-4o-mini...</span>
    </div>
  `;
  stream.appendChild(loadingDiv);
  stream.scrollTop = stream.scrollHeight;
  lucide.createIcons();

  // Prepare FormData
  const fd = new FormData();
  fd.append("messages", JSON.stringify(currentChat.messages));
  if (attachedFile) {
    fd.append("file", attachedFile);
  }

  const sendBtn = document.getElementById("claude-send-btn");
  if (sendBtn) sendBtn.disabled = true;

  try {
    const res = await fetch("/api/ai/chat", {
      method: "POST",
      body: fd
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "AI Chat failed");

    // Remove loading
    const lEl = document.getElementById(loadingId);
    if (lEl) lEl.remove();

    const replyText = data.reply || "No response received.";
    const artifact = data.artifact || null;

    appendClaudeMessageBubble("assistant", replyText, null, artifact);

    currentChat.messages.push({
      role: "assistant",
      content: replyText,
      artifact: artifact
    });
    saveClaudeChatsToStorage();

    if (artifact) {
      displayClaudeArtifact(artifact);
    }

  } catch (err) {
    const lEl = document.getElementById(loadingId);
    if (lEl) lEl.remove();
    appendClaudeMessageBubble("assistant", `⚠️ **Error communicating with GPT-4o-mini:** ${err.message}`);
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    stream.scrollTop = stream.scrollHeight;
    lucide.createIcons();
  }
}

function appendClaudeMessageBubble(role, content, attachmentName = null, artifact = null) {
  const stream = document.getElementById("claude-message-stream");
  if (!stream) return;

  const bubble = document.createElement("div");
  bubble.className = (role === "user") ? "claude-msg-user" : "claude-msg-assistant";

  if (role === "user") {
    let html = "";
    if (attachmentName) {
      html += `<div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0,0,0,0.25); padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; margin-bottom: 6px;"><i data-lucide="paperclip" style="width: 12px; height: 12px;"></i> ${escapeHtml(attachmentName)}</div><br>`;
    }
    html += escapeHtml(content);
    bubble.innerHTML = html;
  } else {
    let rendered = renderMarkdownToHtml(content);
    if (artifact) {
      rendered += `
        <div class="claude-inline-artifact-card" onclick="openArtifactFromMessage(this)">
          <div style="display: flex; align-items: center; gap: 8px;">
            <i data-lucide="layers" style="width: 16px; height: 16px; color: #6366f1;"></i>
            <div>
              <strong style="font-size: 0.82rem; color: #c7d2fe;">${escapeHtml(artifact.title || 'Generated Artifact')}</strong>
              <div style="font-size: 0.7rem; color: #818cf8;">Click to view in split-screen Artifact pane</div>
            </div>
          </div>
          <i data-lucide="chevron-right" style="width: 16px; height: 16px; color: #818cf8;"></i>
        </div>
      `;
      bubble.dataset.artifactJson = JSON.stringify(artifact);
    }
    bubble.innerHTML = rendered;
  }

  stream.appendChild(bubble);
  stream.scrollTop = stream.scrollHeight;
  lucide.createIcons();
}

function openArtifactFromMessage(card) {
  const parent = card.closest(".claude-msg-assistant");
  if (parent && parent.dataset.artifactJson) {
    try {
      const art = JSON.parse(parent.dataset.artifactJson);
      displayClaudeArtifact(art);
    } catch (e) {}
  }
}

function displayClaudeArtifact(art) {
  activeClaudeArtifact = art;
  const drawer = document.getElementById("claude-artifact-drawer");
  const titleEl = document.getElementById("claude-art-title");
  const contentEl = document.getElementById("claude-art-content");
  const badgeCount = document.getElementById("claude-artifact-count");

  if (drawer && titleEl && contentEl) {
    titleEl.innerText = art.title || "Artifact";
    if (art.type === "code") {
      contentEl.innerHTML = `<pre style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; overflow-x: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;"><code>${escapeHtml(art.content)}</code></pre>`;
    } else {
      contentEl.innerHTML = renderMarkdownToHtml(art.content);
    }
    drawer.style.display = "flex";
    if (badgeCount) badgeCount.innerText = "1";
    lucide.createIcons();
  }
}

function closeClaudeArtifact() {
  activeClaudeArtifact = null;
  const drawer = document.getElementById("claude-artifact-drawer");
  if (drawer) drawer.style.display = "none";
}

function copyClaudeArtifact() {
  if (!activeClaudeArtifact || !activeClaudeArtifact.content) return;
  navigator.clipboard.writeText(activeClaudeArtifact.content).then(() => {
    alert("Artifact content copied to clipboard!");
  }).catch(() => {
    alert("Could not copy to clipboard.");
  });
}

function downloadClaudeArtifact() {
  if (!activeClaudeArtifact || !activeClaudeArtifact.content) return;
  const blob = new Blob([activeClaudeArtifact.content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const ext = activeClaudeArtifact.type === "code" ? (activeClaudeArtifact.language === "python" ? "py" : "txt") : "md";
  a.download = (activeClaudeArtifact.title || "artifact").replace(/\s+/g, "_") + "." + ext;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function toggleClaudeSpeechRecognition() {
  const micBtn = document.getElementById("claude-mic-btn");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
    return;
  }

  if (claudeSpeechRecognizer) {
    claudeSpeechRecognizer.stop();
    claudeSpeechRecognizer = null;
    if (micBtn) micBtn.style.color = "#a1a1aa";
    return;
  }

  claudeSpeechRecognizer = new SpeechRecognition();
  claudeSpeechRecognizer.continuous = false;
  claudeSpeechRecognizer.interimResults = false;
  claudeSpeechRecognizer.lang = "en-US";

  if (micBtn) micBtn.style.color = "#ef4444";

  claudeSpeechRecognizer.onresult = function(e) {
    const transcript = e.results[0][0].transcript;
    const input = document.getElementById("claude-prompt-input");
    if (input) {
      input.value = (input.value ? input.value + " " : "") + transcript;
      autoExpandClaudeTextarea(input);
    }
  };

  claudeSpeechRecognizer.onend = function() {
    claudeSpeechRecognizer = null;
    if (micBtn) micBtn.style.color = "#a1a1aa";
  };

  claudeSpeechRecognizer.onerror = function() {
    claudeSpeechRecognizer = null;
    if (micBtn) micBtn.style.color = "#a1a1aa";
  };

  claudeSpeechRecognizer.start();
}

// ==============================================================================
// PCML SMART ASSIGNER STUDIO (Chevron Rules & AutoCAD Blueprint Engine)
// ==============================================================================
let selectedPcmlFiles = [];
let pcmlResultsData = null;
let activePcmlDrawingIndex = 0;

function initPcmlStudio() {
  const dropzone = document.getElementById("pcml-dropzone");
  if (dropzone && !dropzone.dataset.dragInit) {
    dropzone.dataset.dragInit = "true";
    ["dragenter", "dragover"].forEach(eventName => {
      dropzone.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("drag-over");
      });
    });
    ["dragleave", "drop"].forEach(eventName => {
      dropzone.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("drag-over");
      });
    });
    dropzone.addEventListener("drop", e => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length) {
        handlePcmlFilesSelect(dt.files);
      }
    });
  }
}

function handlePcmlFilesSelect(files) {
  if (!files || files.length === 0) return;
  hidePcmlError();

  for (let i = 0; i < files.length; i++) {
    const f = files[i];
    const ext = getFileExtension(f.name).toLowerCase();
    if (ext === "dwg" || ext === "dxf") {
      selectedPcmlFiles.push(f);
    }
  }

  renderPcmlQueue();
  updateCloudEgressMetric();
}

function renderPcmlQueue() {
  const queueWrap = document.getElementById("pcml-queue-container");
  const list = document.getElementById("pcml-file-list");
  const countLabel = document.getElementById("pcml-queue-count-label");
  const submitBtn = document.getElementById("pcml-submit-btn");
  const submitText = document.getElementById("pcml-submit-btn-text");

  if (!queueWrap || !list || !submitBtn) return;

  if (selectedPcmlFiles.length === 0) {
    queueWrap.style.display = "none";
    submitBtn.disabled = true;
    submitText.innerText = "Assign PCMLs & Generate Blueprints";
    return;
  }

  queueWrap.style.display = "block";
  countLabel.innerText = `Staged Isometric Drawings (${selectedPcmlFiles.length})`;
  submitBtn.disabled = false;
  submitText.innerText = selectedPcmlFiles.length > 1 
    ? `Assign PCMLs to ${selectedPcmlFiles.length} Drawings`
    : "Assign PCMLs & Generate Blueprint";

  list.innerHTML = selectedPcmlFiles.map((file, idx) => `
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.85rem; border: 1px solid var(--border-ash); background: var(--bg-bone-subtle); border-radius: var(--radius-sm);">
      <div style="display: flex; align-items: center; gap: 0.6rem; overflow: hidden;">
        <i data-lucide="layers" style="width: 14px; height: 14px; color: #0284c7; flex-shrink: 0;"></i>
        <span style="font-size: 0.82rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(file.name)}</span>
        <span style="font-size: 0.72rem; color: var(--text-muted);">(${formatBytes(file.size)})</span>
      </div>
      <button type="button" class="file-loaded-remove" style="width: 24px; height: 24px;" onclick="removePcmlFile(${idx})" title="Remove drawing">
        <i data-lucide="x" style="width: 12px; height: 12px;"></i>
      </button>
    </div>
  `).join("");

  if (window.lucide) lucide.createIcons();
}

function removePcmlFile(idx) {
  selectedPcmlFiles.splice(idx, 1);
  renderPcmlQueue();
  updateCloudEgressMetric();
}

function clearPcmlQueue() {
  selectedPcmlFiles = [];
  renderPcmlQueue();
  updateCloudEgressMetric();
  const input = document.getElementById("pcml-file-input");
  if (input) input.value = "";
}

function showPcmlError(msg) {
  const banner = document.getElementById("pcml-error-banner");
  const txt = document.getElementById("pcml-error-text");
  if (banner && txt) {
    txt.innerText = msg;
    banner.style.display = "flex";
  }
}

function hidePcmlError() {
  const banner = document.getElementById("pcml-error-banner");
  if (banner) banner.style.display = "none";
}

async function submitPcmlAssign() {
  if (selectedPcmlFiles.length === 0) return;

  hidePcmlError();
  const submitBtn = document.getElementById("pcml-submit-btn");
  const submitText = document.getElementById("pcml-submit-btn-text");
  const progWrap = document.getElementById("pcml-progress-wrap");
  const progFill = document.getElementById("pcml-progress-fill");
  const progStatus = document.getElementById("pcml-prog-status");
  const progPercent = document.getElementById("pcml-prog-percent");
  const resultCard = document.getElementById("pcml-result-card");

  submitBtn.disabled = true;
  submitText.innerText = "Analyzing Drawings & Placing PCMLs...";
  progWrap.style.display = "block";
  if (resultCard) resultCard.style.display = "none";

  let pct = 10;
  progFill.style.width = `${pct}%`;
  progPercent.innerText = `${pct}%`;
  progStatus.innerText = "Scanning deadlegs, low points, and terminal caps...";

  const estSec = Math.max(12, selectedPcmlFiles.length * 10);
  const stepMs = Math.round((estSec * 1000) / 80);

  const timer = setInterval(() => {
    if (pct < 88) {
      pct += 1;
      progFill.style.width = `${pct}%`;
      progPercent.innerText = `${pct}%`;
      if (pct === 30) progStatus.innerText = "Evaluating Chevron IS 85, IS 51 & IS 99 rules...";
      if (pct === 55) progStatus.innerText = "Inserting native PART_PCML hexagonal symbols & callouts...";
      if (pct === 75) progStatus.innerText = "Publishing high-resolution vector PDF blueprints...";
    }
  }, stepMs);

  const plotStyle = document.getElementById("pcml-plot-style")?.value || "acad.ctb";
  const paperSize = document.getElementById("pcml-paper-size")?.value || "ANSI full bleed B (17.00 x 11.00 Inches)";
  const includeHeadings = !!document.getElementById("pcml-opt-headings")?.checked;

  const formData = new FormData();
  selectedPcmlFiles.forEach(f => formData.append("files", f));
  formData.append("include_headings", includeHeadings ? "true" : "false");
  formData.append("plot_style", plotStyle);
  formData.append("paper_size", paperSize);

  try {
    const response = await fetch("/api/pcml/assign", {
      method: "POST",
      body: formData
    });

    clearInterval(timer);
    progFill.style.width = "100%";
    progPercent.innerText = "100%";
    progStatus.innerText = "PCML Assignment Finished!";

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "PCML assignment failed.");
    }

    const data = await response.json();
    pcmlResultsData = data;
    renderPcmlResults(data);

    setTimeout(() => {
      progWrap.style.display = "none";
    }, 400);

  } catch (err) {
    clearInterval(timer);
    progWrap.style.display = "none";
    showPcmlError(err.message || "Failed to process drawings.");
  } finally {
    submitBtn.disabled = false;
    submitText.innerText = "Assign PCMLs & Generate Blueprints";
    if (window.lucide) lucide.createIcons();
  }
}

function renderPcmlResults(data) {
  const resultCard = document.getElementById("pcml-result-card");
  if (!resultCard) return;

  resultCard.style.display = "block";

  // Update summary metrics
  document.getElementById("pcml-res-drawings-count").innerText = data.total_drawings || 1;
  document.getElementById("pcml-res-total-count").innerText = data.total_pcml_count || 0;
  
  const sc = data.summary_counts || {};
  document.getElementById("pcml-res-85a-count").innerText = sc["85A"] || 0;
  document.getElementById("pcml-res-51a-count").innerText = sc["51A"] || 0;
  document.getElementById("pcml-res-85b-count").innerText = sc["85B"] || 0;
  document.getElementById("pcml-res-duration").innerText = `${((data.duration_ms || 0) / 1000).toFixed(1)}s`;

  // Batch ZIP download button
  const batchWrap = document.getElementById("pcml-batch-download-wrap");
  const batchBtn = document.getElementById("pcml-batch-download-btn");
  if (data.batch_zip_url) {
    batchWrap.style.display = "block";
    batchBtn.href = data.batch_zip_url;
  } else {
    batchWrap.style.display = "none";
  }

  // Drawing selector dropdown (if multiple)
  const selWrap = document.getElementById("pcml-drawing-selector-wrap");
  const sel = document.getElementById("pcml-drawing-select");
  if (data.results && data.results.length > 1) {
    selWrap.style.display = "block";
    sel.innerHTML = data.results.map((r, i) => `
      <option value="${i}">${escapeHtml(r.filename)} (${r.pcml_count} PCMLs)</option>
    `).join("");
  } else {
    selWrap.style.display = "none";
  }

  // Display first drawing
  activePcmlDrawingIndex = 0;
  displayActivePcmlDrawing(0);

  resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function onPcmlDrawingChange(val) {
  const idx = parseInt(val, 10);
  activePcmlDrawingIndex = idx;
  displayActivePcmlDrawing(idx);
}

function displayActivePcmlDrawing(idx) {
  if (!pcmlResultsData || !pcmlResultsData.results || !pcmlResultsData.results[idx]) return;

  const item = pcmlResultsData.results[idx];
  const labelEl = document.getElementById("pcml-active-drawing-label");
  const previewImg = document.getElementById("pcml-preview-img");
  const expandBtn = document.getElementById("pcml-preview-expand-btn");
  const dlPdfBtn = document.getElementById("pcml-download-pdf-btn");
  const dlDwgBtn = document.getElementById("pcml-download-dwg-btn");
  const tableBody = document.getElementById("pcml-table-body");
  const tableCount = document.getElementById("pcml-table-count");

  if (labelEl) labelEl.innerText = `${item.filename} (Vector Blueprint)`;

  // Preview Image
  if (item.preview_url) {
    previewImg.src = item.preview_url;
    previewImg.style.display = "block";
  } else if (item.pdf_url) {
    previewImg.src = "";
    previewImg.alt = "Vector PDF Ready. Click 'View Full PDF' to inspect.";
  }

  // Action Buttons
  if (item.pdf_url) {
    expandBtn.href = item.pdf_url;
    expandBtn.style.display = "inline-flex";
    dlPdfBtn.href = item.pdf_url;
    dlPdfBtn.style.display = "inline-flex";
    dlPdfBtn.setAttribute("download", `${item.base_name}_PCML.pdf`);
  } else {
    expandBtn.style.display = "none";
    dlPdfBtn.style.display = "none";
  }

  if (item.dwg_url) {
    dlDwgBtn.href = item.dwg_url;
    dlDwgBtn.style.display = "inline-flex";
    dlDwgBtn.setAttribute("download", `${item.base_name}_PCML.dwg`);
  } else {
    dlDwgBtn.style.display = "none";
  }

  // Populate Table
  const assigns = item.assignments || [];
  tableCount.innerText = assigns.length;

  if (assigns.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="3" style="padding: 1.5rem; text-align: center; color: var(--text-muted);">
          No deadleg or stagnant water damage mechanisms detected on this sheet.
        </td>
      </tr>
    `;
  } else {
    tableBody.innerHTML = assigns.map(a => {
      let badgeColor = "#0284c7";
      let badgeBg = "rgba(2, 132, 199, 0.12)";
      if (a.dm_disp === "85A") { badgeColor = "#e11d48"; badgeBg = "rgba(225, 29, 72, 0.12)"; }
      else if (a.dm_disp === "85B") { badgeColor = "#ea580c"; badgeBg = "rgba(234, 88, 12, 0.12)"; }
      else if (a.dm_disp === "51A") { badgeColor = "#0284c7"; badgeBg = "rgba(2, 132, 199, 0.12)"; }
      else if (a.dm_disp === "51B") { badgeColor = "#0d9488"; badgeBg = "rgba(13, 148, 136, 0.12)"; }
      else if (a.dm_disp === "99") { badgeColor = "#7c3aed"; badgeBg = "rgba(124, 58, 237, 0.12)"; }

      const xFmt = typeof a.x === "number" ? a.x.toFixed(2) : a.x;
      const yFmt = typeof a.y === "number" ? a.y.toFixed(2) : a.y;

      return `
        <tr style="border-bottom: 1px solid var(--border-ash); transition: background 150ms;" onmouseover="this.style.background='var(--bg-bone-subtle)'" onmouseout="this.style.background='transparent'">
          <td style="padding: 8px 10px; white-space: nowrap;">
            <span style="background: ${badgeBg}; color: ${badgeColor}; border: 1px solid ${badgeColor}40; padding: 2px 7px; border-radius: 4px; font-weight: 800; font-size: 0.76rem; display: inline-flex; align-items: center; gap: 4px;">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              </svg>
              ${escapeHtml(a.dm_disp)}
            </span>
          </td>
          <td style="padding: 8px 10px; font-family: monospace; font-size: 0.74rem; color: var(--text-muted); white-space: nowrap;">
            (${xFmt}, ${yFmt})
          </td>
          <td style="padding: 8px 10px;">
            <div style="font-weight: 700; color: var(--text-ink); font-size: 0.76rem;">${escapeHtml(a.callout || a.category || a.dm_disp)}</div>
            <div style="color: var(--text-muted); font-size: 0.72rem; line-height: 1.35; margin-top: 1px;">${escapeHtml(a.reason || '')}</div>
          </td>
        </tr>
      `;
    }).join("");
  }

  if (window.lucide) lucide.createIcons();
}

function resetPcmlStudio() {
  clearPcmlQueue();
  pcmlResultsData = null;
  const resultCard = document.getElementById("pcml-result-card");
  if (resultCard) resultCard.style.display = "none";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function togglePcmlRulesModal(show) {
  const modal = document.getElementById("pcml-rules-modal");
  if (modal) {
    modal.style.display = show ? "flex" : "none";
  }
}

function openPcmlPreviewModal() {
  if (pcmlResultsData && pcmlResultsData.results && pcmlResultsData.results[activePcmlDrawingIndex]) {
    const item = pcmlResultsData.results[activePcmlDrawingIndex];
    if (item.pdf_url) {
      window.open(item.pdf_url, "_blank");
    }
  }
}

