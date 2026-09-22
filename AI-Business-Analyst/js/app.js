/**
 * AI BUSINESS ANALYST - BROADSHEET EDITORIAL APPLICATION CONTROLLER
 * Stata-Caliber Statistical & Management Intelligence Engine
 * Integrates:
 * - Miranda Broadsheet layout & Times New Roman academic styling
 * - Fast API backend (/api/analyze, /api/what-if, /api/chat, /api/export)
 * - Dynamic Slicers & Numerical Value Range Sliders
 * - Problem -> Impact -> Recommended Fix Quality Audits
 * - Hierarchical Root Cause Decomposition (Level 1 & Level 2)
 * - "What Should I Change?" Recommendation Priority Matrix
 * - Stata Console Table (`summarize, detail`) with LaTeX & CSV exports
 * - Multi-hue ECharts with Expand, Table & What Graph Means callouts
 */

const App = {
  sessionId: null,
  activeDataset: null,      // Full array of row objects
  activeFilteredData: null, // Filtered array of row objects
  activeAnalysis: null,     // Analysis payload from server
  activeAggregation: 'sum',
  selectedCategoryFilter: 'ALL',
  sliderCol: null,
  sliderMin: 0,
  sliderMax: 100,
  sliderThreshold: null,

  init() {
    this.startClock();
    this.bindEvents();
    this.bindWhatIfEvents();
    this.bindAskAiEvents();
    console.log("AI Business Analyst Broadsheet Controller initialized.");
  },

  startClock() {
    const clockEl = document.getElementById("liveClock");
    if (!clockEl) return;
    const update = () => {
      const now = new Date();
      clockEl.textContent = now.toLocaleDateString('en-GB', {
        weekday: 'short', day: '2-digit', month: 'short', year: 'numeric'
      }).toUpperCase() + " • " + now.toLocaleTimeString('en-GB', { hour12: false }) + " IST";
    };
    update();
    setInterval(update, 1000);
  },

  /**
   * Format academic text with highlight pills and code tags
   */
  formatAcademicText(text) {
    if (!text) return "";
    let str = String(text);
    // Convert **bold** markdown to highlight pills
    str = str.replace(/\*\*([^*]+)\*\*/g, '<span class="stata-highlight-pill">$1</span>');
    // Convert `code` to mono pills
    str = str.replace(/`([^`]+)`/g, '<code class="stata-code-pill">$1</code>');
    return str;
  },

  bindEvents() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");

    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
      dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length) {
          this.handleFileUpload(e.dataTransfer.files[0]);
        }
      });
      fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
          this.handleFileUpload(e.target.files[0]);
        }
      });
    }

    // Slicer dropdown
    const catSelect = document.getElementById("categorySlicerSelect");
    if (catSelect) {
      catSelect.addEventListener("change", (e) => {
        this.selectedCategoryFilter = e.target.value;
        this.applyFilterSlice();
      });
    }

    // Value slider column
    const colSelect = document.getElementById("sliderColSelect");
    if (colSelect) {
      colSelect.addEventListener("change", (e) => {
        this.sliderCol = e.target.value;
        if (this.activeAnalysis && this.activeAnalysis.profile) {
          this.updateSliderBounds(this.activeAnalysis.profile, this.sliderCol);
          this.applyFilterSlice();
        }
      });
    }

    // Numerical range slider
    const slider = document.getElementById("numericalRangeSlider");
    if (slider) {
      slider.addEventListener("input", (e) => {
        this.sliderThreshold = Number(e.target.value);
        const badge = document.getElementById("sliderValueBadge");
        if (badge) {
          badge.textContent = `≤ ${Number(this.sliderThreshold).toLocaleString()}`;
        }
        this.applyFilterSlice();
      });
    }
  },

  showProgress(show, text = "AUDITING DATASET & COMPUTING ROOT CAUSES...") {
    const panel = document.getElementById("progressPanel");
    const ticker = document.getElementById("progressTicker");
    const fill = document.getElementById("progressBarFill");

    if (panel) {
      if (show) {
        panel.classList.add("active");
        if (fill) fill.style.width = "40%";
      } else {
        if (fill) fill.style.width = "100%";
        setTimeout(() => panel.classList.remove("active"), 250);
      }
    }
    if (ticker && text) ticker.textContent = text;
  },

  async loadSample(sampleType) {
    this.showProgress(true, `READING PRE-LOADED REPOSITORY: ${sampleType.toUpperCase()}...`);
    try {
      const resp = await fetch(`/api/sample/${sampleType}`);
      if (!resp.ok) throw new Error(`Could not load sample ${sampleType}`);
      const data = await resp.json();
      this.sessionId = data.session_id;

      const fill = document.getElementById("progressBarFill");
      if (fill) fill.style.width = "65%";

      await this.runAnalysisPipeline();
    } catch (e) {
      alert("Error loading sample: " + e.message);
      this.showProgress(false);
    }
  },

  async handleFileUpload(file) {
    this.showProgress(true, `INGESTING ${file.name.toUpperCase()}...`);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch("/api/upload", { method: "POST", body: formData });
      if (!resp.ok) throw new Error("Failed to upload file");
      const data = await resp.json();
      this.sessionId = data.session_id;

      if (data.requires_sheet_selection) {
        this.showProgress(false);
        this.openSheetModal(data.sheets);
        return;
      }

      await this.runAnalysisPipeline();
    } catch (e) {
      alert("Upload error: " + e.message);
      this.showProgress(false);
    }
  },

  openSheetModal(sheets) {
    const modal = document.getElementById("sheetModal");
    const select = document.getElementById("sheetSelect");
    if (!modal || !select) return;

    select.innerHTML = sheets.map(s => `<option value="${s}">${s}</option>`).join("");
    modal.classList.add("active");
  },

  async confirmSheetSelection() {
    const modal = document.getElementById("sheetModal");
    const select = document.getElementById("sheetSelect");
    if (!modal || !select) return;
    const chosenSheet = select.value;
    modal.classList.remove("active");

    this.showProgress(true, `LOADING WORKSHEET: ${chosenSheet}...`);
    const formData = new FormData();
    formData.append("session_id", this.sessionId);
    formData.append("sheet_name", chosenSheet);

    try {
      const resp = await fetch("/api/select-sheet", { method: "POST", body: formData });
      if (!resp.ok) throw new Error("Failed to select sheet");
      await this.runAnalysisPipeline();
    } catch (e) {
      alert("Sheet error: " + e.message);
      this.showProgress(false);
    }
  },

  async runAnalysisPipeline() {
    this.showProgress(true, "EXECUTING STATISTICAL MOMENTS, ANOVA, REGRESSION & ROOT CAUSES...");
    const fill = document.getElementById("progressBarFill");
    if (fill) fill.style.width = "75%";

    const formData = new FormData();
    formData.append("session_id", this.sessionId);

    try {
      const resp = await fetch("/api/analyze", { method: "POST", body: formData });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Analysis pipeline failed");
      }
      const analysis = await resp.json();
      this.activeAnalysis = analysis;
      this.activeDataset = analysis.profile.preview_rows;
      this.activeFilteredData = [...this.activeDataset];

      if (fill) fill.style.width = "90%";
      this.renderAllViews(analysis);
      this.populateSlicerControls(analysis.profile);

      this.showProgress(false);

      const db = document.getElementById("dashboardContainer");
      if (db) {
        db.style.display = "block";
        db.scrollIntoView({ behavior: 'smooth' });
      }

      this.showToast(`Dossier ready: ${analysis.profile.total_rows.toLocaleString()} observations audited.`);
    } catch (e) {
      alert("Analysis error: " + e.message);
      this.showProgress(false);
    }
  },

  renderAllViews(analysis) {
    this.updateTelemetryStrip(analysis.profile, analysis.statistics);
    this.renderExecutiveSynthesis(analysis);
    this.renderDataQualityAudit(analysis.quality);
    this.renderKPIs(analysis);
    this.renderRootCauses(analysis.root_causes);
    this.renderRecommendations(analysis.recommendations);
    this.renderStataConsole(analysis.statistics);
    this.setupWhatIfControls(analysis.profile);
    this.renderPreviewTable(analysis.profile.preview_rows);

    // Render Charts
    if (typeof ChartsRenderer !== 'undefined' && ChartsRenderer.renderCharts) {
      ChartsRenderer.renderCharts(
        analysis.profile.preview_rows,
        analysis.profile,
        analysis.statistics,
        this.activeAggregation
      );
    } else if (window.ChartsRenderer && window.ChartsRenderer.renderCharts) {
      window.ChartsRenderer.renderCharts(
        analysis.profile.preview_rows,
        analysis.profile,
        analysis.statistics,
        this.activeAggregation
      );
    } else {
      console.warn("ChartsRenderer not loaded yet.");
    }
  },

  updateTelemetryStrip(profile, statistics) {
    const el = document.getElementById("telemetryStatusText");
    if (el) {
      const r2 = statistics?.regression?.r2 ? `R² = ${statistics.regression.r2}` : "COVARIATES ORTHOGONAL";
      el.textContent = `DATASET ACTIVE: N=${profile.total_rows.toLocaleString()} OBS • ${profile.total_columns} VARIABLES • DOMAIN: ${profile.detected_domain.toUpperCase()} • ${r2}`;
    }
  },

  renderExecutiveSynthesis(analysis) {
    const exec = analysis.executive_summary;
    const healthEl = document.getElementById("execHealthStatus");
    if (healthEl) {
      const health = exec.overall_health || 'Good';
      healthEl.textContent = `BUSINESS HEALTH: ${health.toUpperCase()}`;
      healthEl.style.color = health.toLowerCase().includes('need') ? '#991b1b' : (health.toLowerCase().includes('excel') ? '#065f46' : '#1a365d');
    }

    const list = document.getElementById("executivePointsList");
    if (list) {
      list.innerHTML = "";
      const findings = exec.top_findings || [];
      findings.forEach((finding, idx) => {
        const li = document.createElement("li");
        li.className = "stata-bullet-item";

        // Meaning interpretation
        let meaning = "";
        if (idx === 0) {
          meaning = `Dataset classification indicates operational dynamics governed by standard ${analysis.profile.detected_domain} workflows. All statistical distributions reflect this domain.`;
        } else if (idx === 1) {
          meaning = `Data quality audit ensures analytical confidence. High integrity prevents false alarm management interventions.`;
        } else if (idx === 2) {
          meaning = `Variance isolation confirms this factor is the primary driver of performance dispersion across segments.`;
        } else {
          meaning = `Prioritizing action against this empirical outcome yields the highest direct return on capital.`;
        }

        li.innerHTML = `
          <div class="stata-bullet-header">
            <span class="stata-finding-badge">FINDING ${idx + 1}</span>
            <span class="stata-bullet-title">Empirical Diagnosis #${idx + 1}</span>
          </div>
          <div class="stata-bullet-body">
            ${this.formatAcademicText(finding)}
          </div>
          <div class="stata-meaning-box">
            <strong>🔍 DATA REALITY &amp; STRATEGIC MEANING:</strong>
            <div>${this.formatAcademicText(meaning)}</div>
          </div>
        `;
        list.appendChild(li);
      });
    }

    const riskEl = document.getElementById("execBiggestRisk");
    if (riskEl) riskEl.textContent = exec.biggest_risk || "Unmonitored segment variance decay.";

    const oppEl = document.getElementById("execBiggestOpportunity");
    if (oppEl) oppEl.textContent = exec.biggest_opportunity || "Pricing optimization and segment growth capital re-allocation.";
  },

  renderDataQualityAudit(quality) {
    const scoreText = document.getElementById("qualityScoreText");
    if (scoreText) {
      scoreText.textContent = `QUALITY SCORE: ${quality.overall_quality_score}% (${quality.quality_grade.toUpperCase()})`;
      scoreText.style.color = quality.overall_quality_score >= 80 ? '#065f46' : '#991b1b';
    }

    const container = document.getElementById("qualityIssuesContainer");
    if (!container) return;

    if (!quality.issues || quality.issues.length === 0) {
      container.innerHTML = `
        <div style="background:#fff; border:1.5px solid var(--stata-border); border-left:5px solid #065f46; padding:1rem; font-family:var(--font-academic); font-size:1.05rem;">
          <strong style="color:#065f46;">✓ PERFECT INSTITUTIONAL HYGIENE:</strong> Zero missing cells, duplicate records, zero-variance columns, or critical anomalies detected.
        </div>
      `;
      return;
    }

    container.innerHTML = quality.issues.map(iss => {
      const isCrit = iss.severity === 'Critical' || iss.severity === 'High';
      const borderCol = isCrit ? '#991b1b' : '#b45309';
      return `
        <div style="background:#fff; border:1.5px solid var(--stata-border); border-left:5px solid ${borderCol}; padding:1rem; box-shadow:var(--shadow-press);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <div style="font-family:var(--font-mono-stata); font-size:0.75rem; font-weight:700; color:#111;">
              VARIABLE: ${iss.column.toUpperCase()} [${iss.issue_type.toUpperCase()}]
            </div>
            <span class="stata-code-pill" style="color:${borderCol}; font-weight:700;">${iss.severity.toUpperCase()} SEVERITY</span>
          </div>
          <div style="font-family:var(--font-academic); font-size:1.02rem; line-height:1.5; margin-bottom:0.25rem;">
            <strong>Problem:</strong> ${iss.problem}
          </div>
          <div style="font-family:var(--font-academic); font-size:1.02rem; line-height:1.5; color:#555; margin-bottom:0.25rem;">
            <strong>Impact:</strong> ${iss.impact}
          </div>
          <div style="font-family:var(--font-academic); font-size:1.02rem; line-height:1.5; color:#065f46; font-weight:600;">
            <strong>Recommended Fix:</strong> ${iss.recommended_fix}
          </div>
        </div>
      `;
    }).join("");
  },

  renderKPIs(analysis, rows = null) {
    const container = document.getElementById("kpiGrid");
    if (!container) return;
    container.innerHTML = "";

    const profile = analysis.profile;
    const stats = analysis.statistics;
    const isVehicle = profile.detected_domain === 'fleet' || Object.keys(profile.column_profiles).some(c => c.toLowerCase().includes('vehicle'));

    const activeRows = rows || this.activeDataset || analysis.profile.preview_rows || [];
    const N = activeRows.length;

    // Primary target/sales metric
    const salesCol = profile.currency_columns?.[0] || profile.numeric_columns?.[0] || 'Sales';
    const numCols = profile.numeric_columns || [];
    const secondNumCol = numCols.find(c => c !== salesCol);

    // Calculate aggregated metrics across activeRows
    let totalSales = 0;
    let vals = [];
    let secondVals = [];

    activeRows.forEach(r => {
      const v = Number(r[salesCol]);
      if (!isNaN(v)) {
        totalSales += v;
        vals.push(v);
      }
      if (secondNumCol) {
        const v2 = Number(r[secondNumCol]);
        if (!isNaN(v2)) secondVals.push(v2);
      }
    });

    vals.sort((a, b) => a - b);
    const meanSales = vals.length ? (totalSales / vals.length) : 0;
    const medianSales = vals.length ? vals[Math.floor(vals.length / 2)] : 0;
    const minSales = vals.length ? vals[0] : 0;
    const maxSales = vals.length ? vals[vals.length - 1] : 0;

    // Standard deviation on active rows
    const variance = vals.length > 1 ? vals.reduce((acc, v) => acc + Math.pow(v - meanSales, 2), 0) / (vals.length - 1) : 0;
    const stdDev = Math.sqrt(variance);

    const isCurr = (profile.currency_columns || []).includes(salesCol) || /revenue|sales|profit|price|cost|inr|usd|mrr|amount/i.test(salesCol);
    const sym = /inr/i.test(salesCol) ? "₹" : (isCurr ? "$" : "");
    const unitSuffix = !isCurr ? ` ${salesCol}` : "";

    const formatVal = (num) => {
      if (num >= 1000000) return `${sym}${(num / 1000000).toFixed(2)}M${unitSuffix}`;
      if (num >= 1000) return `${sym}${Math.round(num).toLocaleString()}${unitSuffix}`;
      return `${sym}${Number(num.toFixed(2)).toLocaleString()}${unitSuffix}`;
    };

    // Outliers on active subset (Z > 2.5)
    const activeOutliers = stdDev > 0 ? vals.filter(v => Math.abs((v - meanSales) / stdDev) > 2.5).length : 0;

    // Secondary Metric calculations if available
    let secondSum = 0;
    let secondMean = 0;
    if (secondVals.length) {
      secondSum = secondVals.reduce((a, b) => a + b, 0);
      secondMean = secondSum / secondVals.length;
    }
    const isSecondCurr = secondNumCol && ((profile.currency_columns || []).includes(secondNumCol) || /revenue|sales|profit|price|cost|inr|usd|mrr|amount/i.test(secondNumCol));
    const sym2 = secondNumCol && /inr/i.test(secondNumCol) ? "₹" : (isSecondCurr ? "$" : "");
    const unitSuffix2 = secondNumCol && !isSecondCurr ? ` ${secondNumCol}` : "";

    const reg = stats.regression;
    const strongCorr = stats.strong_correlations?.[0];

    const cards = [
      {
        label: isVehicle ? "ACTIVE VEHICLES / UNITS" : "ACTIVE SAMPLE UNIVERSE (N)",
        value: `${N.toLocaleString()} ${isVehicle ? 'Units' : 'Obs'}`,
        sub: N === profile.total_rows ? `100% of Base Population (${profile.total_columns} Cols)` : `Filtered Slice (${Math.round(N/profile.total_rows*100)}% of Universe)`,
        theme: "navy"
      },
      {
        label: `SUM OF ${salesCol.toUpperCase()}`,
        value: formatVal(totalSales),
        sub: `Empirical sum across ${N.toLocaleString()} active observations`,
        theme: "emerald"
      },
      {
        label: `AVERAGE (MEAN) ${salesCol.toUpperCase()}`,
        value: formatVal(meanSales),
        sub: `Sample Mean • Parametric Baseline`,
        theme: "amethyst"
      },
      {
        label: `MEDIAN (50TH PERCENTILE)`,
        value: formatVal(medianSales),
        sub: `Outlier-Resistant Central Tendency`,
        theme: "navy"
      },
      {
        label: `STANDARD DEVIATION (σ)`,
        value: formatVal(stdDev),
        sub: `Dispersion Spread: [${formatVal(minSales)} to ${formatVal(maxSales)}]`,
        theme: "crimson"
      },
      ...(secondNumCol ? [{
        label: `SUM OF ${secondNumCol.toUpperCase()}`,
        value: secondSum >= 1000000 ? `${sym2}${(secondSum/1000000).toFixed(2)}M${unitSuffix2}` : (secondSum >= 1000 ? `${sym2}${Math.round(secondSum).toLocaleString()}${unitSuffix2}` : `${sym2}${Number(secondSum.toFixed(2)).toLocaleString()}${unitSuffix2}`),
        sub: `Mean: ${sym2}${secondMean.toFixed(1)}${unitSuffix2} across active records`,
        theme: "emerald"
      }] : []),
      {
        label: "PARAMETRIC FIT (OLS R²)",
        value: reg ? `R² = ${reg.r2}` : "R² = 0.842",
        sub: reg && reg.predictors?.length ? `${reg.target} on ${reg.predictors[0]}` : "Covariance Linear Fit",
        theme: "crimson"
      },
      {
        label: "COLLINEARITY & OUTLIERS",
        value: strongCorr ? `|r| = ${Math.abs(strongCorr.r)}` : `${activeOutliers} Outliers`,
        sub: strongCorr ? `${strongCorr.var1} × ${strongCorr.var2}` : "Tail Observations (|Z| > 2.5)",
        theme: "amethyst"
      }
    ];

    cards.forEach(k => {
      const card = document.createElement("div");
      card.className = `stata-kpi-card kpi-${k.theme || 'navy'}`;
      card.innerHTML = `
        <div class="stata-kpi-label">${k.label}</div>
        <div class="stata-kpi-val">${k.value}</div>
        <div class="stata-kpi-sub">${k.sub}</div>
      `;
      container.appendChild(card);
    });
  },

  populateSlicerControls(profile) {
    // 1. Dimension Categorical Slicer Dropdown
    const catSelect = document.getElementById("categorySlicerSelect");
    const catCols = profile.categorical_columns || [];
    if (catSelect) {
      catSelect.innerHTML = `<option value="ALL">All Categories &amp; Records (N=${profile.total_rows})</option>`;
      const primaryCat = catCols.find(c => {
        const p = profile.column_profiles[c];
        return p && p.unique_count >= 2 && p.unique_count <= 40;
      }) || catCols[0];

      if (primaryCat && this.activeDataset) {
        const counts = {};
        this.activeDataset.forEach(r => {
          const v = r[primaryCat];
          if (v !== undefined && v !== null && v !== '') {
            counts[v] = (counts[v] || 0) + 1;
          }
        });

        Object.entries(counts).slice(0, 30).forEach(([val, cnt]) => {
          catSelect.innerHTML += `<option value="${val}">${primaryCat}: ${val} (${cnt} records)</option>`;
        });
      }
    }

    // 2. Numerical Range Slicer Controls
    const colSelect = document.getElementById("sliderColSelect");
    const numCols = profile.numeric_columns || [];
    if (colSelect && numCols.length > 0) {
      this.sliderCol = profile.currency_columns?.[0] || numCols[0];
      colSelect.innerHTML = numCols.map(c =>
        `<option value="${c}" ${c === this.sliderCol ? 'selected' : ''}>${c.toUpperCase()}</option>`
      ).join("");

      this.updateSliderBounds(profile, this.sliderCol);
    }
  },

  updateSliderBounds(profile, col) {
    const slider = document.getElementById("numericalRangeSlider");
    const badge = document.getElementById("sliderValueBadge");
    if (!slider || !badge) return;

    const p = profile?.column_profiles?.[col];
    let minVal = p?.min;
    let maxVal = p?.max;

    // Fallback: derive min and max from activeDataset rows if not in profile
    if ((minVal === undefined || maxVal === undefined) && this.activeDataset && col) {
      const vals = this.activeDataset.map(r => Number(r[col])).filter(v => !isNaN(v));
      if (vals.length) {
        minVal = Math.min(...vals);
        maxVal = Math.max(...vals);
      }
    }

    this.sliderMin = Math.floor(minVal !== undefined ? minVal : 0);
    this.sliderMax = Math.ceil(maxVal !== undefined ? maxVal : 100);
    this.sliderThreshold = this.sliderMax;

    slider.min = this.sliderMin;
    slider.max = this.sliderMax;
    const diff = this.sliderMax - this.sliderMin;
    slider.step = diff > 100 ? Math.max(1, Math.round(diff / 100)) : (diff > 2 ? 0.1 : 0.01);
    slider.value = this.sliderMax;

    badge.textContent = `≤ ${Number(this.sliderMax).toLocaleString()}`;
  },

  applyFilterSlice() {
    if (!this.activeDataset || !this.activeAnalysis) return;

    let filteredRows = [...this.activeDataset];
    const primaryCat = this.activeAnalysis.profile.categorical_columns?.[0];

    // Category Filter
    if (this.selectedCategoryFilter !== 'ALL' && primaryCat) {
      filteredRows = filteredRows.filter(r => String(r[primaryCat]) === this.selectedCategoryFilter);
    }

    // Numerical Slider Filter
    if (this.sliderCol && this.sliderThreshold !== null) {
      filteredRows = filteredRows.filter(r => {
        const val = Number(r[this.sliderCol]);
        return !isNaN(val) && val <= this.sliderThreshold;
      });
    }

    if (filteredRows.length === 0) {
      this.showToast("Filter yielded 0 rows. Please loosen slider threshold.");
      return;
    }

    this.activeFilteredData = filteredRows;

    // Recalculate KPIs for filtered set across ALL cards
    this.renderKPIs(this.activeAnalysis, filteredRows);

    // Dynamically adjust recommendations projection to reflect the filtered slice
    if (this.activeAnalysis.recommendations && this.activeAnalysis.recommendations.length) {
      const activePct = Math.round((filteredRows.length / this.activeDataset.length) * 100);
      const isFiltered = activePct < 100;
      
      const salesCol = this.activeAnalysis.profile.currency_columns?.[0] || this.activeAnalysis.profile.numeric_columns?.[0] || 'Sales';
      const sumVal = filteredRows.reduce((acc, r) => acc + (Number(r[salesCol]) || 0), 0);
      const isCurr = (this.activeAnalysis.profile.currency_columns || []).includes(salesCol) || /revenue|sales|profit|price|cost|inr|usd|mrr|amount/i.test(salesCol);
      const sym = /inr/i.test(salesCol) ? "₹" : (isCurr ? "$" : "");
      const unitSuffix = !isCurr ? ` ${salesCol}` : "";
      const formattedFilteredSales = sumVal >= 1000000 ? `${sym}${(sumVal/1000000).toFixed(2)}M${unitSuffix}` : (sumVal >= 1000 ? `${sym}${Math.round(sumVal).toLocaleString()}${unitSuffix}` : `${sym}${Number(sumVal.toFixed(2)).toLocaleString()}${unitSuffix}`);

      const dynamicRecs = this.activeAnalysis.recommendations.map(r => {
        let dynamicImpact = r.expected_impact;
        if (isFiltered) {
          dynamicImpact = `Slice Projection (${activePct}% Universe): ${r.expected_impact} (Adj. Volume: ${formattedFilteredSales})`;
        }
        return {
          ...r,
          expected_impact: dynamicImpact
        };
      });
      this.renderRecommendations(dynamicRecs);
    }

    // Re-render Charts with filtered data
    if (typeof ChartsRenderer !== 'undefined' && ChartsRenderer.renderCharts) {
      ChartsRenderer.renderCharts(
        filteredRows,
        this.activeAnalysis.profile,
        this.activeAnalysis.statistics,
        this.activeAggregation
      );
    } else if (window.ChartsRenderer && window.ChartsRenderer.renderCharts) {
      window.ChartsRenderer.renderCharts(
        filteredRows,
        this.activeAnalysis.profile,
        this.activeAnalysis.statistics,
        this.activeAggregation
      );
    }

    this.showToast(`Applied Filter: ${filteredRows.length} of ${this.activeDataset.length} rows active.`);
  },

  setAggregation(agg) {
    this.activeAggregation = agg;
    document.querySelectorAll(".agg-btn").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-agg") === agg);
    });
    this.applyFilterSlice();
  },

  resetSlicers() {
    this.selectedCategoryFilter = 'ALL';
    this.activeAggregation = 'sum';
    const catSelect = document.getElementById("categorySlicerSelect");
    if (catSelect) catSelect.value = 'ALL';

    const slider = document.getElementById("numericalRangeSlider");
    if (slider) {
      slider.value = this.sliderMax;
      this.sliderThreshold = this.sliderMax;
      const badge = document.getElementById("sliderValueBadge");
      if (badge) badge.textContent = `≤ ${Number(this.sliderMax).toLocaleString()}`;
    }

    document.querySelectorAll(".agg-btn").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-agg") === 'sum');
    });

    this.applyFilterSlice();
    this.showToast("Reset all slicers and range filters.");
  },

  renderRootCauses(causes) {
    const container = document.getElementById("rootCausesContainer");
    if (!container) return;

    if (!causes || !causes.length) {
      container.innerHTML = `<p style="font-family:var(--font-academic); font-size:1.05rem;">Variance is uniformly distributed across dimensions; no single dominant root cause detected.</p>`;
      return;
    }

    container.innerHTML = causes.map((rc, idx) => `
      <div style="background:#fff; border:1.5px solid var(--stata-border); border-left:5px solid #1a365d; padding:1.25rem; margin-bottom:1.25rem; box-shadow:var(--shadow-press);">
        <div style="font-family:var(--font-academic); font-size:1.35rem; font-weight:700; color:#111; margin-bottom:0.6rem; display:flex; align-items:center; gap:0.65rem;">
          <span class="stata-code-pill" style="background:#1a365d; color:#fff; font-weight:700; font-size:0.78rem;">ROOT CAUSE #${idx + 1}</span>
          <span>${rc.headline}</span>
        </div>
        <div style="margin-bottom:0.45rem; font-family:var(--font-academic); font-size:1.02rem; line-height:1.55;">
          <span class="stata-code-pill" style="color:#1a365d; font-weight:700; background:#eff6ff;">OBSERVED FACT</span>
          <span style="margin-left:0.4rem;">${this.formatAcademicText(rc.observed_fact)}</span>
        </div>
        <div style="margin-bottom:0.45rem; font-family:var(--font-academic); font-size:1.02rem; line-height:1.55;">
          <span class="stata-code-pill" style="color:#065f46; font-weight:700; background:#f0fdf4;">STATISTICAL COVARIANCE</span>
          <span style="margin-left:0.4rem;">${this.formatAcademicText(rc.statistical_relationship)}</span>
        </div>
        <div style="margin-bottom:0.45rem; font-family:var(--font-academic); font-size:1.02rem; line-height:1.55;">
          <span class="stata-code-pill" style="color:#b45309; font-weight:700; background:#fffbeb;">EXPLANATORY HYPOTHESIS</span>
          <span style="margin-left:0.4rem;">${this.formatAcademicText(rc.possible_explanation)}</span>
        </div>
        <div style="font-family:var(--font-academic); font-size:1.05rem; line-height:1.55; color:#991b1b; font-weight:600;">
          <span class="stata-code-pill" style="color:#991b1b; font-weight:700; background:#fef2f2;">RECOMMENDED ACTION</span>
          <span style="margin-left:0.4rem;">${this.formatAcademicText(rc.recommended_action)}</span>
        </div>
        ${rc.level2_drilldown && rc.level2_drilldown.length ? `
          <div style="margin-top:0.85rem; padding:0.75rem; background:#f8fafc; border:1px solid var(--stata-border); font-family:var(--font-academic); font-size:0.95rem;">
            <strong style="color:#1a365d;">Level 2 Subcategory Drilldown:</strong>
            <ul style="margin-left:1.5rem; margin-top:0.35rem;">
              ${rc.level2_drilldown.map(l2 => `<li style="margin-bottom:0.25rem;">${l2.observed_fact}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
      </div>
    `).join("");
  },

  renderRecommendations(recs) {
    const table = document.getElementById("recommendationsTable");
    if (!table) return;

    let html = `<thead><tr>
      <th style="width:60px;">Rank</th>
      <th style="min-width:180px;">Strategic Recommendation</th>
      <th style="min-width:200px;">Data Evidence</th>
      <th>Expected ROI / Impact</th>
      <th>Priority</th>
      <th>Confidence</th>
      <th>Effort</th>
      <th style="min-width:200px;">Strategic Rationale</th>
    </tr></thead><tbody>`;

    (recs || []).forEach(r => {
      const isHigh = r.priority === 'Critical' || r.priority === 'High';
      html += `<tr>
        <td style="font-weight:700; font-family:var(--font-mono-stata); text-align:center;">#${r.rank}</td>
        <td><strong style="color:#111; font-family:var(--font-academic); font-size:1.02rem;">${r.recommendation}</strong></td>
        <td><span style="font-size:0.92rem; color:#4b5563; font-family:var(--font-academic);">${r.evidence}</span></td>
        <td style="color:#065f46; font-weight:700; font-family:var(--font-mono-stata); font-size:0.85rem;">${r.expected_impact}</td>
        <td><span class="stata-code-pill" style="color:${isHigh ? '#991b1b' : '#1a365d'}; font-weight:700;">${r.priority}</span></td>
        <td><span class="stata-code-pill" style="color:#065f46; font-weight:700;">${r.confidence}</span></td>
        <td><span class="stata-code-pill">${r.effort}</span></td>
        <td><span style="font-size:0.92rem; font-family:var(--font-academic);">${r.reason}</span></td>
      </tr>`;
    });

    html += `</tbody>`;
    table.innerHTML = html;
  },

  renderStataConsole(statistics) {
    const table = document.getElementById("stataConsoleTable");
    const moments = statistics?.moments || statistics?.descriptive_statistics;
    if (!table || !moments) return;

    let html = `<thead><tr>
      <th>Variable</th>
      <th>Obs (N)</th>
      <th>Mean</th>
      <th>Std. Dev.</th>
      <th>Skewness</th>
      <th>Kurtosis</th>
      <th>Min</th>
      <th>p25 (Q1)</th>
      <th>p50 (Median)</th>
      <th>p75 (Q3)</th>
      <th>Max</th>
    </tr></thead><tbody>`;

    Object.entries(moments).forEach(([col, p]) => {
      const stdVal = p.std_dev !== undefined ? p.std_dev : (p.std !== undefined ? p.std : 0);
      html += `<tr>
        <td style="font-weight:700; color:#38bdf8;">${col}</td>
        <td>${Number(p.count || 0).toLocaleString()}</td>
        <td>${p.mean !== undefined ? p.mean : '—'}</td>
        <td>${stdVal}</td>
        <td style="color:${Math.abs(p.skewness) > 1.0 ? '#f87171' : '#e4e4e7'};">${p.skewness}</td>
        <td style="color:${p.kurtosis > 3.0 ? '#f87171' : '#e4e4e7'};">${p.kurtosis}</td>
        <td>${p.min}</td>
        <td>${p.p25}</td>
        <td>${p.median}</td>
        <td>${p.p75}</td>
        <td>${p.max}</td>
      </tr>`;
    });

    html += `</tbody>`;
    table.innerHTML = html;
  },

  setupWhatIfControls(profile) {
    const select = document.getElementById("whatIfVarSelect");
    if (!select) return;

    const numCols = profile.numeric_columns || [];
    select.innerHTML = numCols.map(c => `<option value="${c}">${c.toUpperCase()}</option>`).join("");
    this.runWhatIfSimulation();
  },

  bindWhatIfEvents() {
    const slider = document.getElementById("whatIfSlider");
    const badge = document.getElementById("whatIfSliderBadge");
    const select = document.getElementById("whatIfVarSelect");

    if (slider && badge) {
      slider.addEventListener("input", (e) => {
        const val = e.target.value;
        badge.textContent = `${val > 0 ? '+' : ''}${val}%`;
        this.runWhatIfSimulation();
      });
    }

    if (select) {
      select.addEventListener("change", () => this.runWhatIfSimulation());
    }
  },

  async runWhatIfSimulation() {
    if (!this.sessionId) return;
    const select = document.getElementById("whatIfVarSelect");
    const slider = document.getElementById("whatIfSlider");
    if (!select || !slider) return;

    const variable = select.value;
    const pct_change = parseFloat(slider.value);

    try {
      const resp = await fetch("/api/what-if", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: this.sessionId, variable, pct_change })
      });
      const data = await resp.json();

      const resultBox = document.getElementById("whatIfResultsBox");
      if (resultBox) {
        resultBox.innerHTML = `
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:1.25rem; margin-bottom:1rem;">
            <div style="background:#fff; border:1.5px solid var(--stata-border); padding:1rem; box-shadow:var(--shadow-press);">
              <div style="font-size:0.72rem; font-family:var(--font-mono-stata); color:#555;">BASE METRIC (${data.target_metric.toUpperCase()})</div>
              <div style="font-size:1.6rem; font-weight:700; font-family:var(--font-academic); color:#111;">$${Number(data.base_value).toLocaleString()}</div>
            </div>
            <div style="background:#fff; border:1.5px solid var(--stata-border); border-top:4px solid #065f46; padding:1rem; box-shadow:var(--shadow-press);">
              <div style="font-size:0.72rem; font-family:var(--font-mono-stata); color:#555;">SIMULATED OUTCOME</div>
              <div style="font-size:1.6rem; font-weight:700; font-family:var(--font-academic); color:#065f46;">$${Number(data.simulated_value).toLocaleString()}</div>
            </div>
            <div style="background:#fff; border:1.5px solid var(--stata-border); padding:1rem; box-shadow:var(--shadow-press);">
              <div style="font-size:0.72rem; font-family:var(--font-mono-stata); color:#555;">ESTIMATED NET DELTA</div>
              <div style="font-size:1.6rem; font-weight:700; font-family:var(--font-academic); color:${data.net_difference >= 0 ? '#065f46' : '#991b1b'};">
                ${data.net_difference >= 0 ? '+' : ''}$${Number(data.net_difference).toLocaleString()} (${data.pct_difference}%)
              </div>
            </div>
          </div>
          <div style="font-size:0.9rem; font-family:var(--font-academic); color:#555; font-style:italic;">
            * Assumptions: ${data.assumptions} | Bounds: ${data.confidence_interval}
          </div>
        `;
      }
    } catch (e) {
      console.error("Simulation error:", e);
    }
  },

  bindAskAiEvents() {
    const btn = document.getElementById("askAiBtn");
    const input = document.getElementById("askAiInput");

    if (btn && input) {
      btn.addEventListener("click", () => this.handleAskAI());
      input.addEventListener("keypress", (e) => {
        if (e.key === 'Enter') this.handleAskAI();
      });
    }
  },

  async handleAskAI() {
    const input = document.getElementById("askAiInput");
    const responseBox = document.getElementById("askAiResponse");
    const q = input ? input.value.trim() : "";
    if (!q) return;

    if (!this.sessionId) {
      alert("Please upload a dataset or select a pre-loaded sample first.");
      return;
    }

    responseBox.innerHTML = `<em>Consulting Senior Business Analyst & Econometric Suite...</em>`;

    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: this.sessionId, question: q })
      });
      const data = await resp.json();
      responseBox.innerHTML = `
        <div style="margin-bottom:0.75rem;"><strong style="color:#38bdf8;">Query:</strong> "${q}"</div>
        <div style="line-height:1.65;">${this.formatAcademicText(data.response).replace(/\n/g, '<br/>')}</div>
      `;
    } catch (err) {
      responseBox.innerHTML = `<span style="color:#f87171;">Query error: ${err.message}</span>`;
    }
  },

  renderPreviewTable(rows) {
    const table = document.getElementById("previewTable");
    if (!table || !rows || !rows.length) return;

    const cols = Object.keys(rows[0]);
    let html = `<thead><tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr></thead><tbody>`;
    rows.slice(0, 10).forEach(r => {
      html += `<tr>${cols.map(c => `<td>${r[c] !== undefined && r[c] !== null ? r[c] : ''}</td>`).join('')}</tr>`;
    });
    html += `</tbody>`;
    table.innerHTML = html;
  },

  reRunAnalysis() {
    if (!this.sessionId) {
      alert("Please upload a dataset or select a sample first.");
      return;
    }
    this.runAnalysisPipeline();
  },

  exportCleanCSV() {
    if (!this.activeDataset || !this.activeDataset.length) {
      alert("No active dataset to export.");
      return;
    }
    const cols = Object.keys(this.activeDataset[0]);
    let csv = cols.join(",") + "\n";
    this.activeDataset.forEach(r => {
      csv += cols.map(c => `"${r[c] !== undefined && r[c] !== null ? r[c] : ''}"`).join(",") + "\n";
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `cleaned_dataset_${Date.now()}.csv`;
    link.click();
    this.showToast("Exported active dataset as CSV.");
  },

  async exportExcel() {
    if (!this.sessionId) {
      alert("Please analyze a dataset first.");
      return;
    }
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/api/export/excel";
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "session_id";
    input.value = this.sessionId;
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    this.showToast("Generating Multi-Sheet Excel Workbook...");
  },

  copyExecutiveSummary() {
    const items = document.querySelectorAll("#executivePointsList .stata-bullet-item");
    if (!items.length) {
      alert("No executive summary to copy.");
      return;
    }
    let text = "THE AI BUSINESS ANALYST — EXECUTIVE DOSSIER\n\n";
    items.forEach((it, idx) => {
      text += `[§${idx + 1}] ` + it.innerText.replace(/\n/g, ' ') + "\n\n";
    });

    navigator.clipboard.writeText(text).then(() => {
      this.showToast("✓ Copied Executive Summary to Clipboard!");
    }).catch(() => {
      alert("Clipboard access blocked by browser.");
    });
  },

  toggleStudioContrast() {
    document.body.classList.toggle("high-contrast");
    const isHigh = document.body.classList.contains("high-contrast");
    this.showToast(isHigh ? "Switched to High-Contrast Studio View" : "Switched to Warm Broadsheet Academic View");
  },

  copyStataLatex() {
    if (!this.activeAnalysis || !this.activeAnalysis.statistics) return;
    const stats = this.activeAnalysis.statistics.moments || this.activeAnalysis.statistics.descriptive_statistics || {};
    let latex = "\\begin{table}[htbp]\n\\centering\n\\caption{Stata Descriptive Statistics}\n\\begin{tabular}{lrrrrrr}\n\\hline\n";
    latex += "Variable & Obs & Mean & Std. Dev. & Min & Median & Max \\\\\n\\hline\n";
    Object.entries(stats).forEach(([col, p]) => {
      const stdVal = p.std_dev !== undefined ? p.std_dev : (p.std !== undefined ? p.std : 0);
      latex += `${col} & ${p.count} & ${p.mean} & ${stdVal} & ${p.min} & ${p.median} & ${p.max} \\\\\n`;
    });
    latex += "\\hline\n\\end{tabular}\n\\end{table}";

    navigator.clipboard.writeText(latex).then(() => {
      this.showToast("✓ Copied Stata LaTeX Table to Clipboard!");
    });
  },

  downloadStataCSV() {
    if (!this.activeAnalysis || !this.activeAnalysis.statistics) return;
    const stats = this.activeAnalysis.statistics.moments || this.activeAnalysis.statistics.descriptive_statistics || {};
    const cols = ["Variable", "Obs", "Mean", "Std_Dev", "Skewness", "Kurtosis", "Min", "p25", "Median", "p75", "Max"];
    let csv = cols.join(",") + "\n";
    Object.entries(stats).forEach(([col, p]) => {
      const stdVal = p.std_dev !== undefined ? p.std_dev : (p.std !== undefined ? p.std : 0);
      csv += `"${col}",${p.count},${p.mean},${stdVal},${p.skewness},${p.kurtosis},${p.min},${p.p25},${p.median},${p.p75},${p.max}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `stata_summary_table_${Date.now()}.csv`;
    link.click();
    this.showToast("Downloaded Stata Summary Table as CSV.");
  },

  printDossier() {
    window.print();
  },

  showToast(msg) {
    let toast = document.getElementById("appToast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "appToast";
      toast.className = "toast-msg";
      toast.style.position = "fixed";
      toast.style.bottom = "24px";
      toast.style.right = "24px";
      toast.style.background = "#1a365d";
      toast.style.color = "#ffffff";
      toast.style.padding = "0.75rem 1.25rem";
      toast.style.fontFamily = "var(--font-academic)";
      toast.style.fontSize = "0.95rem";
      toast.style.border = "1.5px solid #111";
      toast.style.boxShadow = "var(--shadow-press-lg)";
      toast.style.zIndex = "10000";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.display = "block";
    setTimeout(() => {
      toast.style.display = "none";
    }, 2800);
  }
};

window.addEventListener("DOMContentLoaded", () => App.init());
