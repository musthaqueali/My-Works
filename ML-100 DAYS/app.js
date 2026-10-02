/**
 * THE CAMPUSX MACHINE LEARNING & AI LIBRARY
 * Ultra-Fast Broadsheet Catalog & Prioritized High-Definition Direct-Scroll Engine
 * Zero Quality Loss (HiDPI Vector Precision) & Zero Queue Lag
 */

// Dimensions & Layout
const BASE_WIDTH = 595.276;
const BASE_HEIGHT = 841.89;

// Storage Keys
const STORAGE_THEME = "broadsheet_library_theme";
const STORAGE_SCALE = "broadsheet_library_scale";
const STORAGE_LAST_COURSE = "broadsheet_last_course_id";

// State
let activeView = 'library'; // 'library' | 'reader'
let activeCourse = null;
let pdfDoc = null;
let currentScale = parseFloat(localStorage.getItem(STORAGE_SCALE)) || 1.35;
let currentPage = 1;
let renderedPages = new Map(); // pageNum -> bool
let activeChapterId = 1;
let sidebarCollapsed = false;
let activeCategoryFilter = 'all';

// Prioritized Rendering Queue System
let renderQueue = [];
let isRendering = false;
let currentRenderTask = null;
let currentRenderingPage = null;
let visiblePagesSet = new Set();
let pageObserver = null;

// DOM Cache
const dom = {};

document.addEventListener('DOMContentLoaded', () => {
  // Cache DOM references
  dom.libraryView = document.getElementById('libraryView');
  dom.readerWorkspace = document.getElementById('readerWorkspace');
  dom.scrollContainer = document.getElementById('scrollContainer');
  dom.indexScrollArea = document.getElementById('indexScrollArea');
  dom.coursesGrid = document.getElementById('coursesGrid');
  dom.categoryFilterStrip = document.getElementById('categoryFilterStrip');
  dom.librarySearchInput = document.getElementById('librarySearchInput');
  dom.globalResultsWrap = document.getElementById('globalResultsWrap');
  dom.globalResultsList = document.getElementById('globalResultsList');
  dom.globalResultsCount = document.getElementById('globalResultsCount');
  
  dom.btnBackToLibrary = document.getElementById('btnBackToLibrary');
  dom.courseSwitcher = document.getElementById('courseSwitcher');
  dom.daySelect = document.getElementById('daySelect');
  dom.stepperInput = document.getElementById('stepperInput');
  dom.totalPagesDisplay = document.getElementById('totalPagesDisplay');
  dom.btnPrevPage = document.getElementById('btnPrevPage');
  dom.btnNextPage = document.getElementById('btnNextPage');
  dom.readerSearchInput = document.getElementById('readerSearchInput');
  dom.currentReadingLabel = document.getElementById('currentReadingLabel');
  dom.btnToggleSidebar = document.getElementById('btnToggleSidebar');
  dom.indexPane = document.getElementById('editorialIndexPane');
  dom.btnTheme = document.getElementById('btnTheme');
  dom.btnZoomIn = document.getElementById('btnZoomIn');
  dom.btnZoomOut = document.getElementById('btnZoomOut');
  dom.btnZoomFit = document.getElementById('btnZoomFit');
  dom.initialLoader = document.getElementById('initialLoader');
  dom.toast = document.getElementById('editorialToast');
  dom.progressBar = document.getElementById('readingProgressBar');
  dom.progressText = document.getElementById('readingProgressText');

  // Configure PDF.js worker
  if (window.pdfjsLib) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'pdf.worker.min.js';
  }

  // Apply Theme
  const savedTheme = localStorage.getItem(STORAGE_THEME) || 'light';
  applyTheme(savedTheme);

  // Render Library Cards
  renderLibraryCatalog();

  // Populate Course Switcher in reader top bar
  populateCourseSwitcher();

  // Check URL Hash or Initial Route
  handleInitialRoute();

  // Setup Event Handlers
  setupEvents();
});

// ==========================================================================
// 1. ROUTING & VIEW SWITCHING
// ==========================================================================
function handleInitialRoute() {
  const hash = window.location.hash;
  if (hash) {
    const params = new URLSearchParams(hash.replace('#', ''));
    const courseId = params.get('course');
    const pageNum = parseInt(params.get('page'), 10);

    if (courseId && COURSES_TOC[courseId]) {
      openCourseReader(courseId, !isNaN(pageNum) ? pageNum : 1);
      return;
    }
  }

  showLibraryView();
}

function showLibraryView() {
  activeView = 'library';
  dom.libraryView.style.display = 'block';
  dom.readerWorkspace.classList.remove('active');
  dom.readerWorkspace.style.display = 'none';

  const readerBar = document.getElementById('readerControlsBar');
  if (readerBar) readerBar.style.display = 'none';

  history.replaceState(null, '', window.location.pathname);
  renderLibraryCatalog();
}

function showReaderView() {
  activeView = 'reader';
  dom.libraryView.style.display = 'none';
  dom.readerWorkspace.classList.add('active');
  dom.readerWorkspace.style.display = 'flex';

  const readerBar = document.getElementById('readerControlsBar');
  if (readerBar) readerBar.style.display = 'flex';
}

// ==========================================================================
// 2. LIBRARY CATALOG (Blocks of Notes)
// ==========================================================================
function renderLibraryCatalog() {
  if (!dom.coursesGrid || typeof COURSES_CATALOG === 'undefined') return;

  dom.coursesGrid.innerHTML = '';

  const filtered = COURSES_CATALOG.filter(c => {
    if (activeCategoryFilter === 'all') return true;
    return c.category.toLowerCase().includes(activeCategoryFilter.toLowerCase());
  });

  filtered.forEach(course => {
    const savedPage = localStorage.getItem(`course_progress_${course.id}`) || 1;
    const pct = Math.min(100, Math.round((parseInt(savedPage, 10) / course.pages) * 100));

    const card = document.createElement('div');
    card.className = 'course-card';
    card.onclick = () => openCourseReader(course.id, parseInt(savedPage, 10));

    card.innerHTML = `
      <div>
        <div class="course-card-header">
          <span class="course-vol-badge">${course.vol}</span>
          <span class="course-category-tag">${escapeHtml(course.category)}</span>
        </div>
        <h3 class="course-card-title">${escapeHtml(course.title)}</h3>
        <p class="course-card-subtitle">${escapeHtml(course.subtitle)}</p>
        
        <div class="course-metrics-bar">
          <span><strong>${course.pages.toLocaleString()}</strong> Folios</span>
          <span>•</span>
          <span><strong>${course.topics.toLocaleString()}</strong> Topics</span>
          <span>•</span>
          <span><strong>${course.chaptersCount}</strong> Ch</span>
        </div>

        <p class="course-card-desc">${escapeHtml(course.description)}</p>

        <div class="course-card-tags">
          ${course.badges.map(b => `<span class="topic-tag">${escapeHtml(b)}</span>`).join('')}
        </div>
      </div>

      <div class="course-card-footer">
        <span class="course-progress-badge">
          ${pct > 0 ? `📖 Folio ${savedPage} (${pct}%)` : `✦ Unread (${course.pages} p.)`}
        </span>
        <button class="btn-open-course">
          OPEN DISPATCH →
        </button>
      </div>
    `;

    dom.coursesGrid.appendChild(card);
  });
}

function setupCategoryFilter(category) {
  activeCategoryFilter = category;
  document.querySelectorAll('.pill-filter').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.category === category);
  });
  renderLibraryCatalog();
}

function handleGlobalSearch(query) {
  query = query.toLowerCase().trim();
  if (!query) {
    if (dom.globalResultsWrap) dom.globalResultsWrap.style.display = 'none';
    return;
  }

  const results = [];
  COURSES_CATALOG.forEach(course => {
    const toc = COURSES_TOC[course.id];
    if (toc && toc.flatItems) {
      toc.flatItems.forEach(item => {
        if (item.title.toLowerCase().includes(query)) {
          results.push({
            courseId: course.id,
            courseTitle: course.title,
            courseVol: course.vol,
            topicTitle: item.title,
            page: item.page,
            type: item.type
          });
        }
      });
    }
  });

  if (dom.globalResultsWrap) {
    dom.globalResultsWrap.style.display = 'block';
    dom.globalResultsCount.textContent = `Found ${results.length} topics matching "${query}"`;
    dom.globalResultsList.innerHTML = '';

    results.slice(0, 30).forEach(res => {
      const item = document.createElement('div');
      item.className = 'global-result-item';
      item.innerHTML = `
        <span class="global-result-title">• ${escapeHtml(res.topicTitle)}</span>
        <div class="global-result-meta">
          <span style="color: var(--accent-ember); font-weight: 700;">${res.courseVol}</span>
          <span>${escapeHtml(res.courseTitle)}</span>
          <span class="index-folio-badge">P. ${res.page}</span>
        </div>
      `;
      item.onclick = () => openCourseReader(res.courseId, res.page);
      dom.globalResultsList.appendChild(item);
    });

    if (results.length > 30) {
      const more = document.createElement('div');
      more.style.padding = '8px 12px';
      more.style.fontSize = '11px';
      more.style.color = 'var(--text-muted)';
      more.style.fontFamily = 'var(--font-mono)';
      more.textContent = `...and ${results.length - 30} more matching topics across library.`;
      dom.globalResultsList.appendChild(more);
    }
  }
}

// ==========================================================================
// 3. READING DESK (Active Course Reader)
// ==========================================================================
async function openCourseReader(courseId, targetPage = 1) {
  const course = COURSES_CATALOG.find(c => c.id === courseId);
  if (!course) return;

  activeCourse = course;
  currentPage = targetPage || 1;
  localStorage.setItem(STORAGE_LAST_COURSE, courseId);

  showReaderView();

  if (dom.courseSwitcher) dom.courseSwitcher.value = courseId;
  if (dom.totalPagesDisplay) dom.totalPagesDisplay.textContent = course.pages.toLocaleString();
  if (dom.stepperInput) dom.stepperInput.max = course.pages;

  renderCourseIndex(courseId);
  populateDaySelectForCourse(courseId);

  await loadCoursePdf(course, currentPage);
}

function populateCourseSwitcher() {
  if (!dom.courseSwitcher || typeof COURSES_CATALOG === 'undefined') return;
  dom.courseSwitcher.innerHTML = '';
  COURSES_CATALOG.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = `${c.vol}: ${c.title}`;
    dom.courseSwitcher.appendChild(opt);
  });
}

async function loadCoursePdf(course, targetPage) {
  // Cancel any active render task and clear queues
  cancelCurrentRender();
  renderQueue = [];
  renderedPages.clear();
  visiblePagesSet.clear();

  if (pageObserver) pageObserver.disconnect();

  if (dom.initialLoader) {
    dom.initialLoader.style.display = 'flex';
    dom.initialLoader.style.opacity = '1';
    const sub = document.querySelector('.initial-loader-sub');
    if (sub) sub.textContent = `Connecting to ${course.vol}: ${course.title} (${course.pages} folios)...`;
  }

  try {
    const loadingTask = pdfjsLib.getDocument({
      url: course.filename,
      rangeChunkSize: 65536,
      disableAutoFetch: true,
      disableStream: false
    });

    pdfDoc = await loadingTask.promise;
    console.log(`Loaded ${course.title} (${pdfDoc.numPages} pages).`);

    // Build page wrappers with fixed dimensions (flex-shrink: 0)
    buildPagePlaceholders(pdfDoc.numPages);

    // Setup viewport observer
    setupPageObserver();

    // Hide loader
    if (dom.initialLoader) {
      dom.initialLoader.style.opacity = '0';
      setTimeout(() => { dom.initialLoader.style.display = 'none'; }, 200);
    }

    // Direct jump to target page with highest priority
    setTimeout(() => {
      scrollToPage(targetPage, 'auto');
    }, 60);

  } catch (err) {
    console.error('Error loading course PDF:', err);
    showReaderLoadError(course);
  }
}

function showReaderLoadError(course) {
  if (!dom.initialLoader) return;
  dom.initialLoader.innerHTML = `
    <div style="background-color: var(--bg-bone); border: 2px solid var(--border-ink); padding: 30px; max-width: 540px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
      <div style="font-family: var(--font-display); font-size: 24px; font-weight: 900; color: var(--accent-ember);">
        Fast Launch Recommended
      </div>
      <p style="font-family: var(--font-serif-editorial); font-size: 15px; margin: 12px 0; color: var(--text-charcoal);">
        For instant 0.0s streaming across all 10 volumes, double-click:
      </p>
      <div style="background: var(--bg-parchment); border: 1px dashed var(--border-ink); padding: 10px; font-family: var(--font-mono); font-size: 13px; font-weight: 700; margin-bottom: 16px;">
        ⚡ start_website.bat
      </div>
      <div style="display: flex; justify-content: center; gap: 12px;">
        <button class="btn-broadsheet" onclick="showLibraryView()">← BACK TO LIBRARY</button>
        <button class="btn-broadsheet" onclick="location.reload()">RELOAD</button>
      </div>
    </div>
  `;
}

// Build lightweight layout placeholders for all pages
function buildPagePlaceholders(totalPages) {
  dom.scrollContainer.innerHTML = '';
  const pageW = Math.round(BASE_WIDTH * currentScale);
  const pageH = Math.round(BASE_HEIGHT * currentScale);

  const fragment = document.createDocumentFragment();

  for (let i = 1; i <= totalPages; i++) {
    const wrapper = document.createElement('div');
    wrapper.className = 'folio-page-wrapper';
    wrapper.id = `folio-page-${i}`;
    wrapper.dataset.page = i;
    wrapper.style.width = `${pageW}px`;
    wrapper.style.height = `${pageH}px`;
    wrapper.style.minHeight = `${pageH}px`;
    wrapper.style.maxHeight = `${pageH}px`;

    wrapper.innerHTML = `
      <div class="folio-placeholder" id="placeholder-${i}">
        <div class="folio-loading-spinner"></div>
        <span>FOLIO ${i}</span>
      </div>
      <div class="folio-stamp">FOLIO ${i} / ${totalPages} • ${activeCourse ? activeCourse.vol : ''}</div>
    `;

    fragment.appendChild(wrapper);
  }

  dom.scrollContainer.appendChild(fragment);
}

// ==========================================================================
// 4. HIGH-SPEED PRIORITIZED RENDERING ENGINE (ZERO QUALITY LOSS)
// ==========================================================================
function setupPageObserver() {
  if (pageObserver) pageObserver.disconnect();

  const options = {
    root: dom.scrollContainer,
    rootMargin: '400px 0px', // Buffer 400px around viewport
    threshold: 0.01
  };

  pageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const pageNum = parseInt(entry.target.dataset.page, 10);
      if (entry.isIntersecting) {
        visiblePagesSet.add(pageNum);
        // Request render with priority based on visibility
        enqueuePageRender(pageNum, 100);
      } else {
        visiblePagesSet.delete(pageNum);
      }
    });
  }, options);

  document.querySelectorAll('.folio-page-wrapper').forEach(el => pageObserver.observe(el));

  let scrollTimeout = null;
  dom.scrollContainer.addEventListener('scroll', () => {
    if (scrollTimeout) return;
    scrollTimeout = setTimeout(() => {
      updateActivePageFromScroll();
      scrollTimeout = null;
    }, 50);
  }, { passive: true });
}

function cancelCurrentRender() {
  if (currentRenderTask) {
    try {
      currentRenderTask.cancel();
    } catch (e) {}
    currentRenderTask = null;
  }
  isRendering = false;
  currentRenderingPage = null;
}

// Enqueue a page with a given priority (higher number = rendered first)
function enqueuePageRender(pageNum, priority = 50) {
  if (renderedPages.has(pageNum)) return;

  const existingIdx = renderQueue.findIndex(item => item.pageNum === pageNum);
  if (existingIdx !== -1) {
    if (priority > renderQueue[existingIdx].priority) {
      renderQueue[existingIdx].priority = priority;
      renderQueue.sort((a, b) => b.priority - a.priority);
    }
  } else {
    renderQueue.push({ pageNum, priority });
    renderQueue.sort((a, b) => b.priority - a.priority);
  }

  processRenderQueue();
}

async function processRenderQueue() {
  if (isRendering || renderQueue.length === 0 || !pdfDoc) return;

  const next = renderQueue.shift();
  if (!next) return;

  const pageNum = next.pageNum;
  if (renderedPages.has(pageNum)) {
    processRenderQueue();
    return;
  }

  isRendering = true;
  currentRenderingPage = pageNum;

  const wrapper = document.getElementById(`folio-page-${pageNum}`);
  if (!wrapper) {
    isRendering = false;
    processRenderQueue();
    return;
  }

  try {
    const page = await pdfDoc.getPage(pageNum);

    // ULTRA-HD RETINA RESOLUTION (Zero Clarity Loss)
    // Render at 2.4x - 3.0x pixel density for 300 DPI razor-sharp formulas & diagrams
    const dpr = Math.max(window.devicePixelRatio || 1, 2.4);
    const renderScale = currentScale * dpr;
    const viewport = page.getViewport({ scale: renderScale });

    let canvas = wrapper.querySelector('canvas');
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.className = 'folio-canvas';
      wrapper.appendChild(canvas);
    }

    canvas.width = Math.floor(viewport.width);
    canvas.height = Math.floor(viewport.height);
    canvas.style.width = Math.floor(viewport.width / dpr) + "px";
    canvas.style.height = Math.floor(viewport.height / dpr) + "px";

    const ctx = canvas.getContext('2d', { alpha: false });
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';

    currentRenderTask = page.render({
      canvasContext: ctx,
      viewport: viewport
    });

    await currentRenderTask.promise;

    // Success: hide placeholder spinner
    const placeholder = document.getElementById(`placeholder-${pageNum}`);
    if (placeholder) placeholder.style.display = 'none';

    renderedPages.set(pageNum, true);
  } catch (err) {
    if (err.name !== 'RenderingCancelledException') {
      console.warn(`Render error on page ${pageNum}:`, err);
    }
  } finally {
    isRendering = false;
    currentRenderTask = null;
    currentRenderingPage = null;

    // Immediately process next visible page in queue
    processRenderQueue();
  }
}

// Track active page as user scrolls
function updateActivePageFromScroll() {
  const scrollTop = dom.scrollContainer.scrollTop;
  const pageH = (BASE_HEIGHT * currentScale) + 32;
  const maxPages = activeCourse ? activeCourse.pages : 2434;
  const approxPage = Math.max(1, Math.min(maxPages, Math.floor((scrollTop + 200) / pageH) + 1));

  if (approxPage !== currentPage) {
    currentPage = approxPage;
    updateHeaderPageDisplay(currentPage);
    if (activeCourse) {
      localStorage.setItem(`course_progress_${activeCourse.id}`, currentPage);
      history.replaceState(null, '', `#course=${activeCourse.id}&page=${currentPage}`);
    }

    // Pre-enqueue upcoming adjacent pages with low priority
    if (currentPage + 1 <= maxPages && !renderedPages.has(currentPage + 1)) {
      enqueuePageRender(currentPage + 1, 40);
    }
  }
}

// Instant 0.000s topic jump
function scrollToPage(pageNumber, behavior = 'smooth') {
  let page = parseInt(pageNumber, 10);
  if (isNaN(page)) page = 1;
  const maxPages = activeCourse ? activeCourse.pages : 2434;
  page = Math.max(1, Math.min(maxPages, page));

  currentPage = page;
  if (activeCourse) {
    localStorage.setItem(`course_progress_${activeCourse.id}`, page);
    history.replaceState(null, '', `#course=${activeCourse.id}&page=${page}`);
  }

  // Interrupt whatever offscreen page was rendering and prioritize TARGET page FIRST!
  cancelCurrentRender();
  renderQueue = []; // clear all background backlog

  // Target page gets top priority 1000!
  enqueuePageRender(page, 1000);
  if (page + 1 <= maxPages) enqueuePageRender(page + 1, 800);
  if (page - 1 >= 1) enqueuePageRender(page - 1, 700);

  const targetWrapper = document.getElementById(`folio-page-${page}`);
  if (targetWrapper) {
    targetWrapper.scrollIntoView({ behavior: behavior, block: 'start' });
  } else {
    const pageH = (BASE_HEIGHT * currentScale) + 32;
    dom.scrollContainer.scrollTo({
      top: (page - 1) * pageH,
      behavior: behavior
    });
  }

  updateHeaderPageDisplay(page);
  highlightActiveChapter(page);
}

// ==========================================================================
// 5. TABLE OF CONTENTS FOR ACTIVE COURSE
// ==========================================================================
function renderCourseIndex(courseId, filterQuery = '') {
  if (!dom.indexScrollArea || typeof COURSES_TOC === 'undefined') return;

  const toc = COURSES_TOC[courseId];
  if (!toc) return;

  dom.indexScrollArea.innerHTML = '';
  const query = filterQuery.toLowerCase().trim();

  toc.chapters.forEach(chapter => {
    const chMatch = query === '' || chapter.title.toLowerCase().includes(query) || `ch ${chapter.id}`.includes(query);
    
    const matchingSections = (chapter.sections || []).filter(sec => {
      const secMatch = query === '' || sec.title.toLowerCase().includes(query);
      const subMatch = sec.subsections && sec.subsections.some(sub => query === '' || sub.title.toLowerCase().includes(query));
      return secMatch || subMatch || chMatch;
    });

    if (chMatch || matchingSections.length > 0) {
      const block = document.createElement('div');
      block.className = `index-chapter-block ${query !== '' ? 'expanded' : ''}`;
      block.id = `index-ch-${chapter.id}`;

      const row = document.createElement('div');
      row.className = 'index-chapter-row';
      row.innerHTML = `
        <div class="index-chapter-left">
          <div class="index-chapter-num">Chapter ${chapter.id}</div>
          <div class="index-chapter-title">${escapeHtml(chapter.title)}</div>
        </div>
        <div class="index-folio-badge">P. ${chapter.page}</div>
      `;

      // 0.000s instant jump
      row.addEventListener('click', () => {
        block.classList.toggle('expanded');
        scrollToPage(chapter.page);
      });

      block.appendChild(row);

      if (matchingSections.length > 0) {
        const secList = document.createElement('div');
        secList.className = 'index-sections-list';

        matchingSections.forEach(sec => {
          const secRow = document.createElement('div');
          secRow.className = 'index-section-row';
          secRow.innerHTML = `
            <span class="index-section-title">• ${escapeHtml(sec.title)}</span>
            <span class="index-section-folio">p. ${sec.page}</span>
          `;
          secRow.addEventListener('click', (e) => {
            e.stopPropagation();
            scrollToPage(sec.page);
          });
          secList.appendChild(secRow);
        });

        block.appendChild(secList);
      }

      dom.indexScrollArea.appendChild(block);
    }
  });

  highlightActiveChapter(currentPage);
}

function populateDaySelectForCourse(courseId) {
  if (!dom.daySelect || typeof COURSES_TOC === 'undefined') return;
  const toc = COURSES_TOC[courseId];
  if (!toc) return;

  dom.daySelect.innerHTML = '';
  toc.chapters.forEach(ch => {
    const opt = document.createElement('option');
    opt.value = ch.page;
    opt.textContent = `Ch ${ch.id}: ${ch.title.length > 30 ? ch.title.substring(0, 30) + '...' : ch.title}`;
    dom.daySelect.appendChild(opt);
  });
}

function highlightActiveChapter(page) {
  if (!activeCourse) return;
  const toc = COURSES_TOC[activeCourse.id];
  if (!toc) return;

  let activeCh = null;
  const lookup = toc.chapterLookup || [];
  for (let i = lookup.length - 1; i >= 0; i--) {
    if (page >= lookup[i].page) {
      activeCh = lookup[i];
      break;
    }
  }

  document.querySelectorAll('.index-chapter-row').forEach(el => el.classList.remove('active'));

  if (activeCh) {
    activeChapterId = activeCh.id;
    const block = document.getElementById(`index-ch-${activeCh.id}`);
    if (block) {
      const row = block.querySelector('.index-chapter-row');
      if (row) row.classList.add('active');
    }
    if (dom.daySelect) dom.daySelect.value = activeCh.page;
    if (dom.currentReadingLabel) {
      dom.currentReadingLabel.innerHTML = `<span class="num">${activeCourse.vol} • CH ${activeCh.id}:</span> ${escapeHtml(activeCh.title)}`;
    }
  } else {
    if (dom.currentReadingLabel) {
      dom.currentReadingLabel.innerHTML = `<span class="num">${activeCourse.vol} • FOLIO ${page}:</span> ${escapeHtml(activeCourse.title)}`;
    }
  }

  const total = activeCourse.pages || 2434;
  const pct = Math.min(100, Math.round((page / total) * 100));
  if (dom.progressBar) dom.progressBar.style.width = `${pct}%`;
  if (dom.progressText) dom.progressText.textContent = `${pct}% Read (${page}/${total})`;
}

function updateHeaderPageDisplay(page) {
  if (dom.stepperInput) dom.stepperInput.value = page;
  highlightActiveChapter(page);
}

// ==========================================================================
// 6. ZOOM CONTROLS
// ==========================================================================
function setZoom(newScale) {
  newScale = Math.max(0.85, Math.min(2.2, newScale));
  currentScale = newScale;
  localStorage.setItem(STORAGE_SCALE, newScale);

  const pageW = Math.round(BASE_WIDTH * currentScale);
  const pageH = Math.round(BASE_HEIGHT * currentScale);

  document.querySelectorAll('.folio-page-wrapper').forEach(wrapper => {
    wrapper.style.width = `${pageW}px`;
    wrapper.style.height = `${pageH}px`;
    wrapper.style.minHeight = `${pageH}px`;
    wrapper.style.maxHeight = `${pageH}px`;
  });

  cancelCurrentRender();
  renderedPages.clear();
  renderQueue = [];

  scrollToPage(currentPage, 'auto');
  showToast(`Zoom: ${Math.round(currentScale * 100)}%`);
}

// ==========================================================================
// 7. EVENT LISTENERS
// ==========================================================================
function setupEvents() {
  if (dom.btnBackToLibrary) {
    dom.btnBackToLibrary.addEventListener('click', showLibraryView);
  }

  if (dom.courseSwitcher) {
    dom.courseSwitcher.addEventListener('change', (e) => {
      openCourseReader(e.target.value, 1);
    });
  }

  dom.stepperInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const p = parseInt(dom.stepperInput.value, 10);
      if (!isNaN(p)) scrollToPage(p);
    }
  });

  dom.stepperInput.addEventListener('change', () => {
    const p = parseInt(dom.stepperInput.value, 10);
    if (!isNaN(p)) scrollToPage(p);
  });

  dom.btnPrevPage.addEventListener('click', () => {
    if (currentPage > 1) scrollToPage(currentPage - 1);
  });

  dom.btnNextPage.addEventListener('click', () => {
    const max = activeCourse ? activeCourse.pages : 2434;
    if (currentPage < max) scrollToPage(currentPage + 1);
  });

  if (dom.daySelect) {
    dom.daySelect.addEventListener('change', (e) => {
      const p = parseInt(e.target.value, 10);
      if (!isNaN(p)) scrollToPage(p);
    });
  }

  if (dom.readerSearchInput) {
    dom.readerSearchInput.addEventListener('input', (e) => {
      if (activeCourse) renderCourseIndex(activeCourse.id, e.target.value);
    });
  }

  if (dom.librarySearchInput) {
    dom.librarySearchInput.addEventListener('input', (e) => {
      handleGlobalSearch(e.target.value);
    });
  }

  document.querySelectorAll('.pill-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      setupCategoryFilter(btn.dataset.category);
    });
  });

  if (dom.btnToggleSidebar) {
    dom.btnToggleSidebar.addEventListener('click', () => {
      sidebarCollapsed = !sidebarCollapsed;
      dom.indexPane.classList.toggle('collapsed', sidebarCollapsed);
    });
  }

  const statusToggle = document.getElementById('statusToggleSidebar');
  if (statusToggle) {
    statusToggle.addEventListener('click', () => {
      sidebarCollapsed = !sidebarCollapsed;
      dom.indexPane.classList.toggle('collapsed', sidebarCollapsed);
    });
  }

  const btnNative = document.getElementById('btnOpenNativePdf');
  if (btnNative) {
    btnNative.addEventListener('click', () => {
      if (activeCourse) {
        window.open(`${activeCourse.filename}#page=${currentPage}`, '_blank');
      }
    });
  }

  if (dom.btnZoomIn) dom.btnZoomIn.addEventListener('click', () => setZoom(currentScale + 0.15));
  if (dom.btnZoomOut) dom.btnZoomOut.addEventListener('click', () => setZoom(currentScale - 0.15));
  if (dom.btnZoomFit) dom.btnZoomFit.addEventListener('click', () => {
    const deskW = dom.scrollContainer.clientWidth - 80;
    const fitScale = Math.max(0.95, Math.min(1.8, deskW / BASE_WIDTH));
    setZoom(fitScale);
  });

  if (dom.btnTheme) {
    dom.btnTheme.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      showToast(`${next === 'dark' ? 'Editorial Dark' : 'Warm Parchment'} Mode`);
    });
  }

  window.addEventListener('keydown', (e) => {
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

    if (e.key === 'ArrowLeft' || e.key === '[') {
      if (activeView === 'reader' && currentPage > 1) scrollToPage(currentPage - 1);
    } else if (e.key === 'ArrowRight' || e.key === ']') {
      const max = activeCourse ? activeCourse.pages : 2434;
      if (activeView === 'reader' && currentPage < max) scrollToPage(currentPage + 1);
    } else if (e.key.toLowerCase() === 'l') {
      showLibraryView();
    } else if (e.key.toLowerCase() === 'f') {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen();
      }
    } else if (e.key === '+' || e.key === '=') {
      if (activeView === 'reader') setZoom(currentScale + 0.15);
    } else if (e.key === '-' || e.key === '_') {
      if (activeView === 'reader') setZoom(currentScale - 0.15);
    }
  });

  window.addEventListener('hashchange', handleInitialRoute);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(STORAGE_THEME, theme);
  if (dom.btnTheme) {
    dom.btnTheme.textContent = theme === 'dark' ? '☀️ PARCHMENT' : '🌙 INK DARK';
  }
}

function showToast(msg) {
  if (!dom.toast) return;
  dom.toast.textContent = msg;
  dom.toast.classList.add('show');
  setTimeout(() => dom.toast.classList.remove('show'), 2000);
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
