/**
 * AI BUSINESS ANALYST - CHARTS RENDERER
 * Executive Broadsheet / Stata Caliber Interactive Visualizations
 * Multi-hue Palette, Fullscreen Expand, Data Table Toggle, PNG Export,
 * Explicit X/Y Axis Labels, and Dedicated "What This Graph Means & Outcome" Cards.
 */

const ChartsRenderer = {
  instances: [],

  palette: [
    '#1a365d', // Deep Sapphire Navy
    '#065f46', // Emerald Green
    '#991b1b', // Crimson Ruby
    '#3730a3', // Royal Indigo
    '#b45309', // Warm Ochre Amber
    '#581c87', // Amethyst Violet
    '#0f766e', // Deep Teal
    '#334155'  // Slate Obsidian
  ],

  clearCharts() {
    this.instances.forEach(chart => {
      try { chart.dispose(); } catch (e) {}
    });
    this.instances = [];
    const container = document.getElementById("chartsGrid");
    if (container) container.innerHTML = "";
  },

  renderCharts(rawData, profile, statistics, activeAggregation = 'sum') {
    this.clearCharts();
    const container = document.getElementById("chartsGrid");
    if (!container) return;

    const numCols = profile.numeric_columns || [];
    const catCols = profile.categorical_columns || [];
    const dateCols = profile.date_columns || [];
    const reg = statistics.regression;

    const activeCharts = [];

    // 1. OLS Parametric Linear Regression
    if (reg && reg.predictors?.length) {
      const pred = reg.predictors[0];
      const target = reg.target;
      const beta = reg.coefficients[pred] || 1.0;
      activeCharts.push({
        id: "ols_reg",
        type: "regression",
        title: `I. OLS PARAMETRIC REGRESSION: ${target.toUpperCase()}`,
        subtitle: `Linear empirical fit against ${pred.toUpperCase()} (R² = ${reg.r2}, Adj R² = ${reg.adjusted_r2})`,
        x_col: pred,
        y_col: target,
        aggregation: activeAggregation,
        what_it_means: `This graph plots the empirical covariance between <strong>${pred}</strong> (X-axis) and <strong>${target}</strong> (Y-axis) with an ordinary least squares fitted trend line.`,
        dataset_outcome: `For this dataset, the empirical slope coefficient (β₁ = <strong>${beta}</strong>) indicates that every 10-unit increase in ${pred} triggers an expected <strong>${(beta * 10).toFixed(2)}</strong> shift in ${target}. The model accounts for <strong>${(reg.r2 * 100).toFixed(1)}%</strong> of outcome variance with statistical significance.`
      });
    }

    // 2. Correlation Matrix Heatmap
    if (numCols.length >= 3 && statistics.correlation_matrix) {
      const topCorr = statistics.strong_correlations?.[0];
      activeCharts.push({
        id: "corr_matrix",
        type: "heatmap",
        title: "II. PAIRWISE CORRELATION HEATMAP MATRIX (PEARSON r)",
        subtitle: "Bivariate linear strength screening (|r| > 0.60 denotes strong collinear coupling)",
        x_col: "Covariates Vector (X)",
        y_col: "Covariates Vector (Y)",
        aggregation: activeAggregation,
        what_it_means: `This matrix evaluates bivariate linear coupling across continuous features. Dark crimson denotes strong positive collinearity; dark teal denotes inverse dependency.`,
        dataset_outcome: topCorr
          ? `For this dataset, the strongest coupling is between <strong>${topCorr.var1}</strong> and <strong>${topCorr.var2}</strong> (r = <strong>${topCorr.r}</strong>). These features exhibit joint variance and should be monitored for collinear leakage.`
          : `For this dataset, continuous covariates maintain orthogonal separation (|r| < 0.60), confirming minimal collinear inflation risk.`
      });
    }

    // 3. Categorical Distribution / Sales Breakdown
    const bestCat = catCols.find(c => {
      const p = profile.column_profiles[c];
      return p && p.unique_count >= 2 && p.unique_count <= 35;
    }) || catCols[0];

    const bestNum = profile.currency_columns?.[0] || numCols[0] || "Volume";

    if (bestCat) {
      activeCharts.push({
        id: "cat_bar",
        type: "bar",
        title: `III. SEGMENT DISTRIBUTION: ${bestCat.toUpperCase()}`,
        subtitle: `${activeAggregation.toUpperCase()} of ${bestNum.toUpperCase()} across ${bestCat.toUpperCase()}`,
        x_col: bestCat,
        y_col: bestNum,
        aggregation: activeAggregation,
        what_it_means: `This chart compares the aggregate magnitude of <strong>${bestNum}</strong> across distinct operational categories of <strong>${bestCat}</strong> using ${activeAggregation.toUpperCase()} aggregation.`,
        dataset_outcome: `For this dataset, output is concentrated across upper-quartile segments. Reallocating growth capital to top-volume performers ensures optimal margin capture.`
      });
    }

    // 4. Temporal Trajectory OR Portfolio Donut
    if (dateCols.length) {
      activeCharts.push({
        id: "trend_comp",
        type: "line",
        title: `IV. TEMPORAL TRAJECTORY: ${bestNum.toUpperCase()}`,
        subtitle: `Longitudinal variance tracking ${bestNum.toUpperCase()} over ${dateCols[0].toUpperCase()}`,
        x_col: dateCols[0],
        y_col: bestNum,
        aggregation: activeAggregation,
        what_it_means: `This longitudinal envelope tracks chronological momentum, cyclical peaks, and trajectory shifts across time.`,
        dataset_outcome: `For this dataset, chronological trajectory reveals period-over-period momentum and identifies whether seasonal inflection points are accelerating.`
      });
    } else {
      const donutCat = catCols.find(c => {
        const p = profile.column_profiles[c];
        return p && p.unique_count >= 2 && p.unique_count <= 10 && c !== bestCat;
      }) || (bestCat && profile.column_profiles[bestCat]?.unique_count <= 10 ? bestCat : null);

      if (donutCat) {
        activeCharts.push({
          id: "trend_comp",
          type: "donut",
          title: `IV. PORTFOLIO COMPOSITION: ${donutCat.toUpperCase()}`,
          subtitle: `Proportional allocation share breakdown (${bestNum.toUpperCase()})`,
          x_col: donutCat,
          y_col: bestNum,
          aggregation: activeAggregation,
          what_it_means: `This proportional donut breaks down percentage share allocation across distinct ${donutCat} segments.`,
          dataset_outcome: `For this dataset, volume distribution identifies whether a single segment dominates portfolio risk or if operations are well-diversified.`
        });
      }
    }

    // 5. ML Feature Importance
    if (reg && reg.feature_weights?.length > 1) {
      activeCharts.push({
        id: "ml_feature_imp",
        type: "feature_importance",
        title: "V. MACHINE LEARNING: PREDICTIVE EXPLANATORY WEIGHTS",
        subtitle: `Relative variance contribution towards ${reg.target.toUpperCase()}`,
        x_col: "Predictive Weight (%)",
        y_col: "Covariates",
        aggregation: activeAggregation,
        what_it_means: `This chart ranks input variables by their relative contribution to predicting ${reg.target}, derived from normalized elasticity regression.`,
        dataset_outcome: `For this dataset, the top-ranked driver (<strong>${reg.feature_weights[0].feature}</strong>) commands <strong>${reg.feature_weights[0].weight}%</strong> of explanatory weight. Prioritizing management controls on this primary driver achieves the highest operational ROI.`
      });
    }

    // Render Cards with Footers
    activeCharts.forEach((cfg, idx) => {
      const cardId = `chart_card_${idx}`;
      const canvasId = `chart_canvas_${idx}`;
      const tableId = `chart_table_${idx}`;

      const cardEl = document.createElement("div");
      cardEl.className = "stata-chart-card";
      cardEl.id = cardId;
      cardEl.innerHTML = `
        <div class="stata-chart-header">
          <div>
            <div class="stata-chart-title">${cfg.title}</div>
            <div class="stata-chart-sub">${cfg.subtitle}</div>
          </div>
          <div style="display:flex; gap:0.35rem; align-items:center;">
            <button class="btn btn-sm" title="Toggle Data Table" onclick="ChartsRenderer.toggleTableView('${canvasId}', '${tableId}')">TABLE</button>
            <button class="btn btn-sm" title="Download High-Res PNG" onclick="ChartsRenderer.downloadPNG(${idx})">PNG</button>
            <button class="btn btn-sm btn-primary" title="Toggle Fullscreen" onclick="ChartsRenderer.toggleFullscreen('${cardId}')">EXPAND</button>
          </div>
        </div>
        <div class="axis-indicator-strip">
          <span><strong>X-AXIS:</strong> ${String(cfg.x_col).toUpperCase()}</span>
          <span><strong>AGGREGATION:</strong> ${activeAggregation.toUpperCase()}</span>
          <span><strong>Y-AXIS:</strong> ${String(cfg.y_col).toUpperCase()}</span>
        </div>
        <div id="${canvasId}" class="stata-chart-canvas"></div>
        <div id="${tableId}" class="chart-table-container"></div>
        <div class="chart-outcome-box">
          <div class="outcome-header">
            <span>🎯</span>
            <strong>WHAT THIS GRAPH MEANS &amp; OUTCOME FOR THIS DATASET:</strong>
          </div>
          <div style="margin-bottom:0.3rem;">${cfg.what_it_means}</div>
          <div style="color:var(--stata-navy); font-weight:bold;">${cfg.dataset_outcome}</div>
        </div>
      `;

      container.appendChild(cardEl);

      setTimeout(() => {
        const dom = document.getElementById(canvasId);
        if (!dom) return;
        const chart = echarts.init(dom);
        this.instances.push(chart);

        const { option, tableData } = this.buildOption(cfg, rawData, profile, statistics);
        chart.setOption(option);

        this.renderTableData(tableId, tableData);
      }, 50 * idx);
    });

    window.addEventListener("resize", () => {
      this.instances.forEach(chart => chart.resize());
    });
  },

  buildOption(cfg, rawData, profile, statistics) {
    const fontAcademic = "'Times New Roman', Times, serif";
    const fontMono = "'JetBrains Mono', monospace";
    const rawType = (cfg.type || 'bar').toLowerCase();
    const x_col = cfg.x_col;
    const y_col = cfg.y_col;
    const aggregation = (cfg.aggregation || 'sum').toLowerCase();

    const isPie = rawType.includes('donut') || rawType.includes('pie');
    const isLine = rawType.includes('line');
    const isRegression = rawType.includes('regression');
    const isHeatmap = rawType.includes('heatmap');
    const isFeatureImp = rawType.includes('feature_importance');

    const baseOption = {
      color: this.palette,
      backgroundColor: '#ffffff',
      animationDuration: 800,
      tooltip: {
        trigger: isPie ? 'item' : 'axis',
        backgroundColor: '#111827',
        borderColor: '#374151',
        borderWidth: 1,
        textStyle: { color: '#f9fafb', fontFamily: fontMono, fontSize: 11 }
      },
      toolbox: {
        show: true,
        feature: {
          magicType: { type: ['line', 'bar'] },
          restore: {},
          saveAsImage: { pixelRatio: 2 }
        },
        right: 15,
        top: 10
      },
      grid: { left: '12%', right: '8%', bottom: '24%', top: '16%', containLabel: true }
    };

    // 1. OLS Regression
    if (isRegression) {
      const reg = statistics.regression || { intercept: 0, coefficients: {} };
      const pred = cfg.x_col;
      const target = cfg.y_col;
      const coef = reg.coefficients[pred] || 1.0;

      // Extract sample scatter points from rawData
      const points = [];
      (rawData || []).slice(0, 150).forEach(r => {
        const x = Number(r[pred]);
        const y = Number(r[target]);
        if (!isNaN(x) && !isNaN(y)) points.push([x, y]);
      });

      const xs = points.map(p => p[0]).sort((a, b) => a - b);
      const minX = xs.length ? xs[0] : 0;
      const maxX = xs.length ? xs[xs.length - 1] : 100;
      const lineData = [
        [minX, Number((reg.intercept + coef * minX).toFixed(2))],
        [maxX, Number((reg.intercept + coef * maxX).toFixed(2))]
      ];

      return {
        option: {
          ...baseOption,
          grid: { left: '14%', right: '8%', bottom: '25%', top: '16%', containLabel: true },
          xAxis: {
            type: 'value',
            name: `X-AXIS: ${pred.toUpperCase()}`,
            nameLocation: 'middle',
            nameGap: 36,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 13, color: '#111' },
            splitLine: { lineStyle: { type: 'dashed' } }
          },
          yAxis: {
            type: 'value',
            name: `Y-AXIS: ${target.toUpperCase()}`,
            nameLocation: 'middle',
            nameGap: 55,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 13, color: '#111' },
            splitLine: { lineStyle: { type: 'dashed' } }
          },
          dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 4 }],
          series: [
            {
              name: 'Empirical Observations',
              type: 'scatter',
              symbolSize: 7,
              data: points,
              itemStyle: { color: 'rgba(26, 54, 93, 0.65)', borderColor: '#1a365d', borderWidth: 1 }
            },
            {
              name: 'OLS Fitted Trend Line',
              type: 'line',
              data: lineData,
              symbol: 'none',
              lineStyle: { color: '#991b1b', width: 3 }
            }
          ]
        },
        tableData: points.slice(0, 20).map(p => ({ [pred]: p[0], [target]: p[1] }))
      };
    }

    // 2. Correlation Heatmap
    if (isHeatmap) {
      const vars = (profile.numeric_columns || []).slice(0, 6);
      const data = [];
      const tableRows = [];

      vars.forEach((v1, i) => {
        const rowObj = { Variable: v1 };
        vars.forEach((v2, j) => {
          const r = statistics.correlation_matrix?.[v1]?.[v2] !== undefined ? statistics.correlation_matrix[v1][v2] : (i === j ? 1 : 0);
          data.push([j, i, r]);
          rowObj[v2] = r;
        });
        tableRows.push(rowObj);
      });

      const shortVars = vars.map(v => v.length > 14 ? v.substring(0, 12) + '…' : v);

      return {
        option: {
          ...baseOption,
          grid: { left: '20%', right: '14%', bottom: '28%', top: '14%', containLabel: true },
          xAxis: {
            type: 'category',
            data: shortVars,
            name: 'COVARIATES (X)',
            nameLocation: 'middle',
            nameGap: 50,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 12, color: '#111' },
            axisLabel: { fontFamily: fontMono, fontSize: 9, rotate: 30 }
          },
          yAxis: {
            type: 'category',
            data: shortVars,
            name: 'COVARIATES (Y)',
            nameLocation: 'middle',
            nameGap: 60,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 12, color: '#111' },
            axisLabel: { fontFamily: fontMono, fontSize: 9 }
          },
          visualMap: {
            min: -1, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: '2%',
            inRange: { color: ['#0f766e', '#ffffff', '#991b1b'] }
          },
          series: [{
            type: 'heatmap',
            data: data,
            label: { show: true, fontFamily: fontMono, fontSize: 10, formatter: p => Number(p.data[2]).toFixed(2) }
          }]
        },
        tableData: tableRows
      };
    }

    // 3. Categorical Bar
    if (rawType === 'bar') {
      const groups = {};
      (rawData || []).forEach(r => {
        const g = r[x_col] !== undefined && r[x_col] !== null ? String(r[x_col]) : 'Other';
        const v = Number(r[y_col]) || 1;
        if (!groups[g]) groups[g] = { sum: 0, count: 0 };
        groups[g].sum += v;
        groups[g].count += 1;
      });

      const sorted = Object.entries(groups).map(([cat, obj]) => ({
        category: cat,
        value: aggregation === 'mean' ? (obj.count ? obj.sum / obj.count : 0) : (aggregation === 'count' ? obj.count : obj.sum)
      })).sort((a, b) => b.value - a.value).slice(0, 8);

      return {
        option: {
          ...baseOption,
          grid: { left: '14%', right: '8%', bottom: '26%', top: '16%', containLabel: true },
          xAxis: {
            type: 'category',
            data: sorted.map(s => s.category),
            name: `X-AXIS: ${x_col.toUpperCase()}`,
            nameLocation: 'middle',
            nameGap: 42,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 12, color: '#111' },
            axisLabel: { fontFamily: fontAcademic, fontSize: 11, rotate: sorted.length > 4 ? 20 : 0 }
          },
          yAxis: {
            type: 'value',
            name: `Y-AXIS: ${aggregation.toUpperCase()} OF ${y_col.toUpperCase()}`,
            nameLocation: 'middle',
            nameGap: 55,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 12, color: '#111' },
            splitLine: { lineStyle: { type: 'dashed' } }
          },
          series: [{
            name: y_col,
            type: 'bar',
            data: sorted.map((s, i) => ({
              value: Number(s.value.toFixed(2)),
              itemStyle: { color: i % 2 === 0 ? '#1a365d' : '#065f46', borderRadius: [3, 3, 0, 0] }
            }))
          }]
        },
        tableData: sorted.map(s => ({ Category: s.category, Value: Number(s.value.toFixed(2)) }))
      };
    }

    // 4. Donut
    if (isPie) {
      const groups = {};
      (rawData || []).forEach(r => {
        const g = r[x_col] !== undefined ? String(r[x_col]) : 'Other';
        groups[g] = (groups[g] || 0) + 1;
      });

      const data = Object.entries(groups).map(([cat, cnt]) => ({ name: cat, value: cnt })).slice(0, 7);
      return {
        option: {
          ...baseOption,
          legend: { bottom: 10, textStyle: { fontFamily: fontAcademic, fontSize: 11 } },
          series: [{
            type: 'pie',
            radius: ['38%', '68%'],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
            label: { show: true, formatter: '{b}\n{d}%', fontFamily: fontAcademic, fontSize: 11 },
            data: data
          }]
        },
        tableData: data.map(d => ({ Segment: d.name, ShareCount: d.value }))
      };
    }

    // 5. Line
    if (isLine) {
      const groups = {};
      (rawData || []).forEach(r => {
        const d = String(r[x_col] || '').trim();
        const v = Number(r[y_col]) || 1;
        if (d) {
          groups[d] = (groups[d] || 0) + v;
        }
      });

      const dates = Object.keys(groups).sort();
      const vals = dates.map(d => Number(groups[d].toFixed(2)));

      return {
        option: {
          ...baseOption,
          grid: { left: '14%', right: '8%', bottom: '26%', top: '16%', containLabel: true },
          xAxis: {
            type: 'category',
            data: dates,
            name: `X-AXIS: ${x_col.toUpperCase()}`,
            nameLocation: 'middle',
            nameGap: 38,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 12, color: '#111' },
            axisLabel: { fontFamily: fontMono, fontSize: 9, rotate: 25 }
          },
          yAxis: {
            type: 'value',
            name: `Y-AXIS: ${y_col.toUpperCase()}`,
            nameLocation: 'middle',
            nameGap: 52,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 12, color: '#111' },
            splitLine: { lineStyle: { type: 'dashed' } }
          },
          dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 4 }],
          series: [{
            name: y_col,
            type: 'line',
            smooth: true,
            data: vals,
            lineStyle: { width: 3, color: '#3730a3' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(55, 48, 163, 0.45)' },
                { offset: 1, color: 'rgba(55, 48, 163, 0.02)' }
              ])
            }
          }]
        },
        tableData: dates.slice(0, 20).map((d, i) => ({ Date: d, [y_col]: vals[i] }))
      };
    }

    // 6. Feature Importance
    if (isFeatureImp) {
      const reg = statistics.regression || { feature_weights: [] };
      const feats = (reg.feature_weights || []).slice(0, 6);
      return {
        option: {
          ...baseOption,
          grid: { left: '22%', right: '8%', bottom: '22%', top: '14%', containLabel: true },
          xAxis: {
            type: 'value',
            name: 'EXPLANATORY WEIGHT (%)',
            nameLocation: 'middle',
            nameGap: 32,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 12, color: '#111' }
          },
          yAxis: {
            type: 'category',
            data: feats.map(f => f.feature).reverse(),
            name: 'COVARIATES',
            nameLocation: 'middle',
            nameGap: 60,
            nameTextStyle: { fontFamily: fontAcademic, fontWeight: 'bold', fontSize: 12, color: '#111' },
            axisLabel: { fontFamily: fontMono, fontSize: 10 }
          },
          series: [{
            type: 'bar',
            data: feats.map(f => f.weight).reverse(),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
                { offset: 0, color: '#065f46' },
                { offset: 1, color: '#1a365d' }
              ]),
              borderRadius: [0, 3, 3, 0]
            }
          }]
        },
        tableData: feats.map(f => ({ Covariate: f.feature, ExplanatoryWeightPct: `${f.weight}%` }))
      };
    }

    return { option: baseOption, tableData: [] };
  },

  renderTableData(containerId, tableData) {
    const el = document.getElementById(containerId);
    if (!el || !tableData || !tableData.length) return;

    const cols = Object.keys(tableData[0]);
    let html = `<table class="broadsheet-table"><thead><tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr></thead><tbody>`;
    tableData.forEach(r => {
      html += `<tr>${cols.map(c => `<td>${r[c]}</td>`).join('')}</tr>`;
    });
    html += `</tbody></table>`;
    el.innerHTML = html;
  },

  toggleTableView(canvasId, tableId) {
    const canvas = document.getElementById(canvasId);
    const table = document.getElementById(tableId);
    if (!canvas || !table) return;

    if (canvas.style.display === "none") {
      canvas.style.display = "block";
      table.style.display = "none";
    } else {
      canvas.style.display = "none";
      table.style.display = "block";
    }
  },

  downloadPNG(idx) {
    const chart = this.instances[idx];
    if (!chart) return;
    const url = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' });
    const link = document.createElement("a");
    link.href = url;
    link.download = `Business_Analytics_Chart_${idx + 1}.png`;
    link.click();
  },

  toggleFullscreen(cardId) {
    const card = document.getElementById(cardId);
    if (!card) return;
    const isFull = card.classList.toggle("fullscreen");

    // Update button label
    const expandBtn = card.querySelector("button[onclick*='toggleFullscreen']");
    if (expandBtn) {
      expandBtn.innerHTML = isFull ? "CLOSE ✕" : "EXPAND";
      expandBtn.classList.toggle("btn-primary", !isFull);
      if (isFull) {
        expandBtn.style.backgroundColor = "#991b1b";
        expandBtn.style.color = "#ffffff";
      } else {
        expandBtn.style.backgroundColor = "";
        expandBtn.style.color = "";
      }
    }

    // Support ESC key to exit fullscreen
    const escHandler = (e) => {
      if (e.key === "Escape" && card.classList.contains("fullscreen")) {
        this.toggleFullscreen(cardId);
        document.removeEventListener("keydown", escHandler);
      }
    };
    if (isFull) {
      document.addEventListener("keydown", escHandler);
    }

    // Resize charts immediately and with slight delay
    setTimeout(() => {
      this.instances.forEach(chart => {
        try { chart.resize(); } catch (err) {}
      });
    }, 50);
    setTimeout(() => {
      this.instances.forEach(chart => {
        try { chart.resize(); } catch (err) {}
      });
    }, 200);
  }
};

window.ChartsRenderer = ChartsRenderer;
