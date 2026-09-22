/* ==========================================================================
   CHEVRON DAILY OPERATIONS TRACKER - ENGINE & CLOUD DBMS
   Real-Time Multi-User Cloud Synchronization, Live Machine Learning & DBMS
   Compatible with both local file:/// protocol and HTTP/HTTPS servers
   ========================================================================== */

function getLocalDateStr(d) {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function getMonday(d) {
    const date = new Date(d);
    const day = date.getDay();
    return new Date(date.setDate(date.getDate() - day + (day === 0 ? -6 : 1)));
}

const DEFAULT_MEMBERS = [
    { id: 'musthaque_ali', name: 'Musthaque Ali', role: 'Reliability Data Analyst', location: 'Global' },
    { id: 'anjani_dara', name: 'Anjani Dara', role: 'Reliability Data Analyst', location: 'Global' },
    { id: 'hana_sayed', name: 'Hana Sayed', role: 'Reliability Data Analyst - India', location: 'India' },
    { id: 'mounika_pasunuti', name: 'Mounika Pasunuti', role: 'Reliability Data Analyst', location: 'Global' },
    { id: 'piyush_gupta', name: 'Piyush Gupta', role: 'Reliability Data Analyst - India', location: 'India' },
    { id: 'priti_barman', name: 'Priti Barman', role: 'Reliability Data Analyst - India', location: 'India' },
    { id: 'sandip_dey', name: 'Sandip Dey', role: 'Reliability Data Analyst - India', location: 'India' },
    { id: 'sayan_adhikary', name: 'Sayan Adhikary', role: 'Reliability Data Analyst - India', location: 'India' },
    { id: 'shivakumar_sunkari', name: 'Shivakumar Sunkari', role: 'Reliability Data Analyst', location: 'Global' },
    { id: 'soumen_jit', name: 'Soumen Jit', role: 'Reliability Data Analyst - India', location: 'India' },
    { id: 'srivalli_sunkari', name: 'Srivalli Sunkari', role: 'Reliability Data Analyst', location: 'Global' },
    { id: 'swapna_santhapuram', name: 'Swapna Santhapuram', role: 'Lead (Services) - India', location: 'India' }
];

function getInitialDemoTasks() {
    const today = getLocalDateStr(new Date());
    return [
        {
            id: 'task_demo_1',
            memberId: 'musthaque_ali',
            date: today,
            description: 'Analyzed flange type calculations and verified material traceability SK1 drawing',
            assets: 'Tank X-3109, Unit 4',
            thingsRequired: 'Tank X-3109, Unit 4',
            hours: 5.75,
            metricHours: 0.25,
            countPerDay: 10,
            achievedOnDay: 6,
            efficiency: '60%',
            roadblocks: '',
            notes: 'Verified thickness against minimum allowable limits',
            category: 'Calculations & Thickness Review',
            status: 'in_progress',
            priority: 'high',
            isHighlighted: true,
            isLabour: true
        },
        {
            id: 'task_demo_2',
            memberId: 'anjani_dara',
            date: today,
            description: 'Reviewed external visual inspection reports 04-21-2008 and 12-19-2017',
            assets: 'DWG-SK1, ISO-48291',
            thingsRequired: 'DWG-SK1, ISO-48291',
            hours: 4.0,
            metricHours: 0.5,
            countPerDay: 8,
            achievedOnDay: 8,
            efficiency: '100%',
            roadblocks: '',
            notes: 'All corrosion markers cross-checked',
            category: 'Visual Inspection Analysis',
            status: 'completed',
            priority: 'normal',
            isHighlighted: false,
            isLabour: true
        },
        {
            id: 'task_demo_3',
            memberId: 'mounika_pasunuti',
            date: today,
            description: 'Did Tank Datamining and component makeup breakdown',
            assets: 'X-3109 unit',
            thingsRequired: 'X-3109 unit',
            hours: 3.5,
            metricHours: 0.5,
            countPerDay: 6,
            achievedOnDay: 5,
            efficiency: '83%',
            roadblocks: 'Awaiting client updated isometric drawing',
            notes: 'Initial datamining passes complete',
            category: 'Tank Datamining',
            status: 'blocked',
            priority: 'critical',
            isHighlighted: true,
            isLabour: false
        }
    ];
}

function loadLocalCache() {
    try {
        const raw = localStorage.getItem('chevron_tasks_cache');
        if (raw !== null) {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) {
                state.allTasksCache = parsed;
                return true;
            }
        }
    } catch(e) {}
    return false;
}

function saveLocalCache() {
    try {
        localStorage.setItem('chevron_tasks_cache', JSON.stringify(state.allTasksCache));
    } catch(e) {}
}

const state = {
    members: [...DEFAULT_MEMBERS],
    tasks: [],
    allTasksCache: [],
    activeDate: getLocalDateStr(new Date()),
    activeTab: 'feed',
    currentTimesheetMonday: getMonday(new Date()),
    searchTerm: '',
    filterMember: 'all',
    filterStatus: 'all',
    dbmsSearchTerm: '',
    firebaseConnected: false,
    biTimeframe: 'all',
    biMember: 'all',
    tsMemberFilter: 'all',
    currentUserMemberId: null,
    drilldownMemberId: null
};

const biCharts = {
    chargeCodes: null,
    teamWorkload: null,
    velocityTrend: null,
    statusPriority: null
};

let dbFirebase = null;

/* ==========================================================================
   MACHINE LEARNING (ML) ENGINE
   ========================================================================== */
const MLEngine = {
    categoryVocab: {
        "Tank Datamining": [
            "tank", "mining", "datamining", "x-3109", "storage", "nozzle", "shell", "bottom", 
            "course", "internal", "roof", "annular", "pad", "api 650", "api 653"
        ],
        "Visual Inspection Analysis": [
            "visual", "inspection", "external", "cui", "corrosion", "pitting", "coating", 
            "crack", "blister", "weld", "ndt", "ut", "ultrasonic", "photo", "report"
        ],
        "Calculations & Thickness Review": [
            "calculation", "thickness", "tmin", "flange", "rating", "asme", "mawp", "stress", 
            "minimum", "required", "head", "cylinder", "joint", "sec viii"
        ],
        "Drawings & Traceability": [
            "drawing", "dwg", "sk1", "isometric", "ga", "traceability", "blueprint", "p&id", 
            "metalforms", "bundle", "sheet", "fabrication", "assembly"
        ],
        "Damage Mechanism Review": [
            "damage", "mechanism", "api 571", "api 580", "htha", "creep", "erosion", "sulfidation", 
            "fatigue", "embrittlement", "cracking", "corrosion rate"
        ],
        "QA / QC Verification": [
            "qa", "qc", "verify", "validation", "audit", "certificate", "mtr", "signoff", 
            "compliance", "check", "quality", "standard"
        ],
        "Reporting & Deliverables": [
            "report", "deliverable", "summary", "client", "slides", "executive", "handover", 
            "deck", "presentation", "timesheet"
        ],
        "Team Standup & Coordination": [
            "standup", "sprint", "meeting", "sync", "coordination", "scrum", "lead", "alignment", 
            "call", "review", "kickoff"
        ]
    },

    classifyTask(text) {
        if (!text || text.trim().length === 0) {
            return { category: "Calculations & Thickness Review", confidence: 0.50, complexity: 5.0 };
        }

        const lower = text.toLowerCase();
        const scores = {};
        let totalScore = 0;

        for (const [cat, keywords] of Object.entries(this.categoryVocab)) {
            let score = 0.05;
            keywords.forEach(kw => {
                if (lower.includes(kw)) score += (kw.length > 5 ? 2.5 : 1.5);
            });
            scores[cat] = score;
            totalScore += score;
        }

        let bestCat = "Calculations & Thickness Review";
        let maxScore = -1;
        for (const [cat, sc] of Object.entries(scores)) {
            if (sc > maxScore) {
                maxScore = sc;
                bestCat = cat;
            }
        }

        const confidence = Math.min(0.98, Math.max(0.65, maxScore / totalScore * 1.8));
        const words = text.trim().split(/\s+/).length;
        const complexity = Math.min(10.0, Math.max(2.0, (words * 0.25) + (maxScore * 0.6)));

        return {
            category: bestCat,
            confidence: parseFloat(confidence.toFixed(2)),
            complexity: parseFloat(complexity.toFixed(1))
        };
    },

    detectWorkloadAnomalies(members, dayTasks) {
        const loads = {};
        members.forEach(m => {
            loads[m.id] = { name: m.name, hours: 0, blockedCount: 0 };
        });

        dayTasks.forEach(t => {
            if (loads[t.memberId]) {
                loads[t.memberId].hours += parseFloat(t.hours) || 0;
                if (t.status === 'blocked') loads[t.memberId].blockedCount += 1;
            }
        });

        const anomalies = [];
        for (const [mId, d] of Object.entries(loads)) {
            if (d.hours >= 8.5) {
                anomalies.push({ type: 'OVERLOAD_ALERT', message: `${d.name} logged ${d.hours.toFixed(1)}h (Overtime Risk)` });
            }
            if (d.blockedCount >= 2) {
                anomalies.push({ type: 'BLOCKED_BOTTLENECK', message: `${d.name} has ${d.blockedCount} blocked tasks` });
            }
        }

        return { anomalies, isHealthy: anomalies.length === 0 };
    },

    generateStandupText(members, tasks, activeDate, format = 'slack') {
        const completed = tasks.filter(t => t.status === 'completed');
        const inProgress = tasks.filter(t => t.status === 'in_progress');
        const blocked = tasks.filter(t => t.status === 'blocked');
        const totalHours = tasks.reduce((sum, t) => sum + (parseFloat(t.hours) || 0), 0);

        if (format === 'bullet') {
            let out = `CHEVRON TEAM DAILY STANDUP — ${activeDate}\n`;
            out += `Total Hours: ${totalHours.toFixed(1)}h | Active Tasks: ${tasks.length}\n\n`;
            
            out += `KEY ACHIEVEMENTS:\n`;
            if (completed.length === 0) out += `• None logged yet.\n`;
            completed.forEach(t => {
                const mem = members.find(m => m.id === t.memberId)?.name || t.memberId;
                out += `• [${mem}] ${t.description} (${t.hours}h)\n`;
            });

            out += `\nIN PROGRESS:\n`;
            if (inProgress.length === 0) out += `• None in progress.\n`;
            inProgress.forEach(t => {
                const mem = members.find(m => m.id === t.memberId)?.name || t.memberId;
                out += `• [${mem}] ${t.description} (${t.hours}h)\n`;
            });

            out += `\nBLOCKERS / REQUIRED ITEMS:\n`;
            if (blocked.length === 0) out += `• None (All paths clear).\n`;
            blocked.forEach(t => {
                const mem = members.find(m => m.id === t.memberId)?.name || t.memberId;
                out += `• 🛑 [${mem}] ${t.description} — Needs: ${t.thingsRequired || 'Client approval'}\n`;
            });

            return out;
        }

        // Slack / Teams
        let out = `*🚀 CHEVRON OPERATIONS DAILY DIGEST | ${activeDate}*\n`;
        out += `*Total Hours:* \`${totalHours.toFixed(1)}h\` | *Completed:* \`${completed.length}\` | *Blocked:* \`${blocked.length}\`\n\n`;

        out += `*✅ Accomplishments:*\n`;
        if (completed.length === 0) out += `_No completed tasks recorded._\n`;
        completed.forEach(t => {
            const mem = members.find(m => m.id === t.memberId)?.name || t.memberId;
            out += `• *${mem}*: ${t.isHighlighted ? '⭐ ' : ''}${t.description} \`(${t.hours}h)\`\n`;
        });

        out += `\n*⏳ In Progress:*\n`;
        if (inProgress.length === 0) out += `_No active tasks in progress._\n`;
        inProgress.forEach(t => {
            const mem = members.find(m => m.id === t.memberId)?.name || t.memberId;
            out += `• *${mem}*: ${t.description} \`(${t.hours}h)\`\n`;
        });

        out += `\n*🛑 Blockers & Things Required:*\n`;
        if (blocked.length === 0) out += `_✅ No blockers flagged today._\n`;
        blocked.forEach(t => {
            const mem = members.find(m => m.id === t.memberId)?.name || t.memberId;
            out += `• ⚠️ *${mem}*: ${t.description}\n  ↳ *Needs:* \`${t.thingsRequired || 'Pending review'}\`\n`;
        });

        return out;
    }
};

/* ==========================================================================
   DATA STORE & PERMANENT CLOUD DBMS LAYER
   ========================================================================== */
const dataStore = {
    async init() {
        // 1. Initialize Firebase Realtime Database if configured and available
        if (typeof firebase !== 'undefined' && window.FIREBASE_CONFIG && window.FIREBASE_CONFIG.apiKey) {
            try {
                if (!firebase.apps.length) {
                    firebase.initializeApp(window.FIREBASE_CONFIG);
                }
                dbFirebase = firebase.database();
                state.firebaseConnected = true;
                
                // Real-time live listener on tasks
                dbFirebase.ref('tasks').on('value', (snapshot) => {
                    const data = snapshot.val();
                    if (data) {
                        state.allTasksCache = Array.isArray(data) ? data : Object.values(data);
                    } else if (!localStorage.getItem('chevron_has_initialized')) {
                        state.allTasksCache = getInitialDemoTasks();
                        localStorage.setItem('chevron_has_initialized', 'true');
                    }
                    saveLocalCache();
                    refreshAll();
                });

                // Real-time live listener on members
                dbFirebase.ref('members').on('value', (snapshot) => {
                    const data = snapshot.val();
                    if (data) {
                        state.members = Array.isArray(data) ? data : Object.values(data);
                    } else {
                        state.members = [...DEFAULT_MEMBERS];
                    }
                    populateMemberDropdowns();
                    renderExcelMemberTabs(state.tasks);
                    refreshAll();
                });

                console.log("[DBMS] Connected to Google Firebase Realtime Database.");
            } catch (e) {
                console.warn("[DBMS] Firebase connection fallback to local/REST:", e);
                state.firebaseConnected = false;
            }
        } else {
            console.log("[DBMS] Running in Standalone / Local Mode.");
        }

        // 2. Load members from backend REST / local fallback
        await this.loadMembers();
    },

    async loadMembers() {
        try {
            const res = await fetch('/api/members');
            if (res.ok) state.members = await res.json();
            else if (!state.members.length) state.members = [...DEFAULT_MEMBERS];
        } catch (e) {
            if (!state.members.length) state.members = [...DEFAULT_MEMBERS];
        }
    },

    async getTasks(dateStr) {
        if (dateStr) {
            return (state.allTasksCache || []).filter(t => t.date === dateStr);
        }
        return state.allTasksCache || [];
    },

    async getAllTasks() {
        return state.allTasksCache || [];
    },

    async saveTask(taskData) {
        if (!taskData.id) {
            taskData.id = "task_" + Math.random().toString(36).substr(2, 9) + "_" + Date.now();
            taskData.createdAt = new Date().toISOString();
        } else {
            taskData.updatedAt = new Date().toISOString();
        }

        // Save to Firebase Cloud
        if (state.firebaseConnected && dbFirebase) {
            try {
                await dbFirebase.ref('tasks/' + taskData.id).set(taskData);
            } catch (err) {
                console.warn("[DBMS] Firebase set error:", err);
            }
        }

        // Also sync to Express REST API if available
        try {
            if (taskData.updatedAt) {
                await fetch(`/api/tasks/${taskData.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(taskData)
                });
            } else {
                await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(taskData)
                });
            }
        } catch (e) {}

        // Update local cache
        const idx = state.allTasksCache.findIndex(t => t.id === taskData.id);
        if (idx >= 0) state.allTasksCache[idx] = taskData;
        else state.allTasksCache.push(taskData);

        saveLocalCache();
        return taskData;
    },

    async deleteTask(taskId) {
        if (state.firebaseConnected && dbFirebase) {
            try {
                await dbFirebase.ref('tasks/' + taskId).remove();
            } catch (e) {}
        }
        try {
            await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
        } catch (e) {}
        state.allTasksCache = state.allTasksCache.filter(t => t.id !== taskId);
        saveLocalCache();
        return true;
    },

    async importFullDatabase(dbJSON) {
        if (!dbJSON || !Array.isArray(dbJSON.members) || !Array.isArray(dbJSON.tasks)) {
            throw new Error("Invalid JSON structure. Must contain 'members' and 'tasks' arrays.");
        }

        // 1. Sync to Firebase
        if (state.firebaseConnected && dbFirebase) {
            const tasksMap = {};
            dbJSON.tasks.forEach(t => tasksMap[t.id] = t);
            const membersMap = {};
            dbJSON.members.forEach(m => membersMap[m.id] = m);

            await dbFirebase.ref('tasks').set(tasksMap);
            await dbFirebase.ref('members').set(membersMap);
        }

        // 2. Sync to Backend REST API
        try {
            await fetch('/api/db/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dbJSON)
            });
        } catch (e) {}

        state.members = dbJSON.members;
        state.allTasksCache = dbJSON.tasks;
        return { members: dbJSON.members.length, tasks: dbJSON.tasks.length };
    },

    async resetDatabaseToDefault() {
        const seedData = {
            members: DEFAULT_MEMBERS,
            tasks: []
        };
        return await this.importFullDatabase(seedData);
    }
};

/* ==========================================================================
   UI RENDERING FUNCTIONS
   ========================================================================== */

function getAvatarDetails(member) {
    if (!member) return { initials: '??', colorClass: 'color-0' };
    const parts = member.name.split(' ');
    const initials = (parts[0]?.[0] || '') + (parts[parts.length - 1]?.[0] || '');
    let hash = 0;
    for (let i = 0; i < member.id.length; i++) hash = member.id.charCodeAt(i) + ((hash << 5) - hash);
    return { initials: initials.toUpperCase(), colorClass: `color-${Math.abs(hash) % 8}` };
}

function getAvatarHTML(member, sizeClass = 'avatar-dot') {
    if (!member) return `<div class="${sizeClass}">??</div>`;
    if (member.avatarUrl) {
        return `<div class="${sizeClass}" style="background-image: url('${member.avatarUrl}');"></div>`;
    }
    const { initials, colorClass } = getAvatarDetails(member);
    return `<div class="${sizeClass} ${colorClass}">${initials}</div>`;
}

const MEMBER_TAB_NAMES = {
    'mounika_pasunuti': 'Mounika',
    'hana_sayed': 'Hana',
    'shivakumar_sunkari': 'Shiva',
    'priti_barman': 'Priti',
    'sayan_adhikary': 'Savan',
    'soumen_jit': 'Soumen',
    'musthaque_ali': 'Musthaque',
    'srivalli_sunkari': 'Silvalif',
    'anjani_dara': 'Anjani',
    'sandip_dey': 'Sandip',
    'piyush_gupta': 'Piyush',
    'swapna_santhapuram': 'Swapna'
};

function getMemberShortName(member) {
    if (!member) return 'Analyst';
    if (MEMBER_TAB_NAMES[member.id]) return MEMBER_TAB_NAMES[member.id];
    return member.name.split(' ')[0];
}

function updateSummaryKPIs(tasks) {
    const isFiltered = state.filterMember && state.filterMember !== 'all';
    const displayTasks = isFiltered ? tasks.filter(t => t.memberId === state.filterMember) : tasks;

    let totalHours = 0;
    let highlightCount = 0;
    let laborHours = 0;
    let totalTarget = 0;
    let totalAchieved = 0;
    let roadblocksCount = 0;
    const activeMembers = new Set();

    displayTasks.forEach(t => {
        const h = parseFloat(t.hours) || 0;
        totalHours += h;
        if (t.isHighlighted) highlightCount++;
        if (t.isLabour) laborHours += h;
        if (h > 0) activeMembers.add(t.memberId);

        let target = parseFloat(t.countPerDay) || 0;
        const metric = parseFloat(t.metricHours) || 0.25;
        if (target <= 0 && h > 0 && metric > 0) {
            target = Math.round(h / metric);
        }
        const achieved = parseFloat(t.achievedOnDay) || 0;
        if (target > 0) totalTarget += target;
        if (achieved > 0) totalAchieved += achieved;

        if (t.roadblocks && t.roadblocks.trim().length > 0) {
            roadblocksCount++;
        }
    });

    const hoursEl = document.getElementById('stat-total-hours');
    if (hoursEl) hoursEl.innerText = totalHours.toFixed(1);

    const activeEl = document.getElementById('stat-active-count');
    if (activeEl) {
        activeEl.innerText = activeMembers.size;
        const sub = activeEl.parentElement.querySelector('.metric-sub');
        if (sub) {
            sub.innerText = isFiltered
                ? (activeMembers.size > 0 ? '/ 1 active' : '/ 1 inactive')
                : `/ ${state.members.length || 12}`;
        }
    }

    const tasksEl = document.getElementById('stat-highlighted-tasks');
    if (tasksEl) tasksEl.innerText = displayTasks.length;

    const achievedEl = document.getElementById('stat-achieved-count');
    if (achievedEl) achievedEl.innerText = `${totalAchieved} / ${totalTarget}`;

    const labelEff = document.getElementById('label-efficiency');
    if (labelEff) {
        labelEff.innerText = isFiltered ? 'Analyst Efficiency' : 'Team Efficiency';
    }

    const effEl = document.getElementById('stat-avg-efficiency');
    if (effEl) {
        if (totalTarget > 0) {
            const avgPct = Math.round((totalAchieved / totalTarget) * 100);
            effEl.innerText = `${avgPct}%`;
            effEl.style.color = avgPct >= 80 ? '#16a34a' : avgPct >= 50 ? '#d97706' : '#dc2626';
        } else {
            effEl.innerText = '-';
            effEl.style.color = '';
        }
    }

    const roadEl = document.getElementById('stat-roadblocks-count');
    if (roadEl) {
        roadEl.innerText = roadblocksCount;
        roadEl.style.color = roadblocksCount > 0 ? 'var(--status-red)' : '';
    }

    // Tile 7: Billable / Direct Production Hours
    const billableEl = document.getElementById('stat-billable-hours');
    const billableSubEl = document.getElementById('stat-billable-sub');
    if (billableEl) billableEl.innerText = laborHours.toFixed(1);
    if (billableSubEl) {
        const bPct = totalHours > 0 ? Math.round((laborHours / totalHours) * 100) : 0;
        billableSubEl.innerText = `hrs (${bPct}%)`;
    }

    // Tile 8: Management Review / Highlights
    const mgmtEl = document.getElementById('stat-mgmt-highlights');
    if (mgmtEl) {
        mgmtEl.innerText = highlightCount;
        if (highlightCount > 0) {
            mgmtEl.style.color = 'var(--status-amber)';
        } else {
            mgmtEl.style.color = '';
        }
    }

    const legacyLaborEl = document.getElementById('stat-labor-tasks');
    if (legacyLaborEl) {
        const avgHours = activeMembers.size > 0 ? (totalHours / activeMembers.size).toFixed(1) : '0.0';
        legacyLaborEl.innerText = avgHours;
    }

    const countFeedEl = document.getElementById('count-feed-tasks');
    if (countFeedEl) countFeedEl.innerText = displayTasks.length;
}

const ORDERED_MEMBER_IDS = [
    'mounika_pasunuti',
    'hana_sayed',
    'shivakumar_sunkari',
    'priti_barman',
    'sayan_adhikary',
    'soumen_jit',
    'musthaque_ali',
    'srivalli_sunkari',
    'anjani_dara',
    'sandip_dey',
    'piyush_gupta',
    'swapna_santhapuram'
];

function renderExcelMemberTabs(allDayTasks = state.tasks) {
    const container = document.getElementById('excel-member-tabs');
    if (!container) return;
    container.innerHTML = '';

    // "All Members" tab
    const allTab = document.createElement('div');
    allTab.className = `excel-tab-item ${state.filterMember === 'all' ? 'active' : ''}`;
    allTab.innerHTML = `<span>All Members</span><span class="excel-tab-count">${allDayTasks.length}</span>`;
    allTab.addEventListener('click', () => {
        state.filterMember = 'all';
        const sel = document.getElementById('db-filter-member');
        if (sel) sel.value = 'all';
        updateSummaryKPIs(allDayTasks);
        renderExcelMemberTabs(allDayTasks);
        renderFeedTable(allDayTasks);
    });
    container.appendChild(allTab);

    // Individual Member tabs matching the exact screenshot sequence
    ORDERED_MEMBER_IDS.forEach(mId => {
        const m = state.members.find(x => x.id === mId);
        if (!m) return;
        const shortName = getMemberShortName(m);
        const memTasks = allDayTasks.filter(t => t.memberId === m.id);
        const tab = document.createElement('div');
        tab.className = `excel-tab-item ${state.filterMember === m.id ? 'active' : ''}`;
        tab.innerHTML = `<span>${shortName}</span><span class="excel-tab-count">${memTasks.length}</span>`;
        tab.addEventListener('click', () => {
            state.filterMember = m.id;
            const sel = document.getElementById('db-filter-member');
            if (sel) sel.value = m.id;
            updateSummaryKPIs(allDayTasks);
            renderExcelMemberTabs(allDayTasks);
            renderFeedTable(allDayTasks);
        });
        container.appendChild(tab);
    });
}

function renderFeedTable(tasks) {
    const tbody = document.getElementById('master-tasks-tbody');
    const emptyState = document.getElementById('table-empty-state');
    if (!tbody) return;
    tbody.innerHTML = '';

    const filtered = tasks.filter(t => {
        const member = state.members.find(m => m.id === t.memberId);
        const memName = member ? member.name.toLowerCase() : '';
        const search = state.searchTerm.toLowerCase();

        const matchSearch = !search || 
            t.description.toLowerCase().includes(search) || 
            memName.includes(search) || 
            (t.category && t.category.toLowerCase().includes(search)) ||
            (t.assets && t.assets.toLowerCase().includes(search)) ||
            (t.thingsRequired && t.thingsRequired.toLowerCase().includes(search)) ||
            (t.roadblocks && t.roadblocks.toLowerCase().includes(search)) ||
            (t.notes && t.notes.toLowerCase().includes(search));

        const matchMember = state.filterMember === 'all' || t.memberId === state.filterMember;
        const matchStatus = state.filterStatus === 'all' || t.status === state.filterStatus;

        return matchSearch && matchMember && matchStatus;
    });

    if (filtered.length === 0) {
        if (emptyState) emptyState.style.display = 'block';
        return;
    }
    if (emptyState) emptyState.style.display = 'none';

    filtered.forEach((task, idx) => {
        const member = state.members.find(m => m.id === task.memberId);
        const tr = document.createElement('tr');

        const sNo = idx + 1;
        const taskDate = task.date || state.activeDate;
        const workerName = member ? member.name : task.memberId;
        const assetsVal = task.assets || task.thingsRequired || '';
        let assetsHTML = `<span class="roadblock-none">—</span>`;
        if (assetsVal.trim().length > 0) {
            const items = assetsVal.split(/[,;]+/).map(s => s.trim()).filter(Boolean);
            assetsHTML = `<div class="req-chips-list">${items.map(it => `<span class="req-chip">${escapeHTML(it)}</span>`).join('')}</div>`;
        }

        const hrs = parseFloat(task.hours) || 0;
        const metricVal = (task.metricHours !== undefined && task.metricHours !== null && task.metricHours !== '') ? task.metricHours : '0.25';
        let countNum = (task.countPerDay !== undefined && task.countPerDay !== null && task.countPerDay !== '') ? parseFloat(task.countPerDay) : null;
        if ((isNaN(countNum) || countNum <= 0) && hrs > 0 && parseFloat(metricVal) > 0) {
            countNum = Math.round(hrs / parseFloat(metricVal));
        }
        const countVal = (countNum !== null && !isNaN(countNum)) ? countNum : '—';
        const achievedVal = (task.achievedOnDay !== undefined && task.achievedOnDay !== null && task.achievedOnDay !== '') ? task.achievedOnDay : '—';

        let effNum = null;
        let effText = task.efficiency || '';
        const achNum = (task.achievedOnDay !== undefined && task.achievedOnDay !== null && task.achievedOnDay !== '') ? parseFloat(task.achievedOnDay) : null;

        if (countNum !== null && countNum > 0 && achNum !== null && !isNaN(achNum)) {
            effNum = Math.round((achNum / countNum) * 100);
            effText = `${effNum}%`;
        } else if (effText && effText.includes('%')) {
            effNum = parseInt(effText);
        }

        let effBadgeHTML = `<span class="eff-badge eff-badge-none">—</span>`;
        if (effText && effText !== '—') {
            const effClass = (effNum !== null && effNum >= 80) ? 'eff-badge-high' : (effNum !== null && effNum >= 50) ? 'eff-badge-mid' : 'eff-badge-low';
            effBadgeHTML = `<span class="eff-badge ${effClass}">${escapeHTML(effText)}</span>`;
        }

        let roadblocksHTML = `<span class="roadblock-none">—</span>`;
        if (task.roadblocks && task.roadblocks.trim().length > 0) {
            roadblocksHTML = `<span class="roadblock-badge" title="${escapeHTML(task.roadblocks)}">⚠️ ${escapeHTML(task.roadblocks)}</span>`;
        }

        let notesHTML = `<span class="roadblock-none">—</span>`;
        if (task.notes && task.notes.trim().length > 0) {
            notesHTML = `<span title="${escapeHTML(task.notes)}" style="font-size: 12px; color: var(--text-secondary); line-height: 1.3;">${escapeHTML(task.notes)}</span>`;
        }

        const statusMap = {
            'completed': { label: 'Completed', class: 'completed' },
            'in_progress': { label: 'In Progress', class: 'in_progress' },
            'blocked': { label: 'On Hold', class: 'blocked' },
            'review': { label: 'Under Review', class: 'review' }
        };
        const st = statusMap[task.status] || statusMap['completed'];
        const priority = task.priority || 'normal';
        const priorityLabel = priority.charAt(0).toUpperCase() + priority.slice(1);

        tr.innerHTML = `
            <td class="text-center" style="font-weight: 600; color: var(--text-muted); font-family: var(--font-mono);">${sNo}</td>
            <td style="font-family: var(--font-mono); font-size: 12px; white-space: nowrap;">${escapeHTML(taskDate)}</td>
            <td>
                <div class="member-chip">
                    ${getAvatarHTML(member, 'avatar-dot')}
                    <span class="member-chip-name">${escapeHTML(workerName)}</span>
                </div>
            </td>
            <td>
                <div style="line-height: 1.4; font-weight: 500;">${escapeHTML(task.description)}</div>
                <div style="display: flex; gap: 6px; align-items: center; margin-top: 3px; flex-wrap: wrap;">
                    <span class="cat-pill">${escapeHTML(task.category || 'General')}</span>
                    ${task.isHighlighted ? '<span style="font-size: 9px; color: var(--status-amber); text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">[Mgmt Review]</span>' : ''}
                    ${task.isLabour ? '<span style="font-size: 9px; color: var(--status-blue); text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">[Billable]</span>' : ''}
                </div>
            </td>
            <td>${assetsHTML}</td>
            <td class="text-right">
                <strong style="font-family: var(--font-mono);">${hrs.toFixed(2)}</strong>
            </td>
            <td class="text-right" style="font-family: var(--font-mono); color: var(--text-secondary);">
                ${metricVal}
            </td>
            <td class="text-center" style="font-family: var(--font-mono); font-weight: 600;">
                ${countVal}
            </td>
            <td class="text-center" style="font-family: var(--font-mono); font-weight: 600;">
                ${achievedVal}
            </td>
            <td class="text-center">
                ${effBadgeHTML}
            </td>
            <td>${roadblocksHTML}</td>
            <td>${notesHTML}</td>
            <td class="text-center">
                <span class="status-badge ${st.class}">${st.label}</span>
                <span style="display: block; font-size: 10px; text-transform: uppercase; font-weight: 600; margin-top: 2px; color: ${priority === 'critical' ? 'var(--status-red)' : priority === 'high' ? 'var(--status-amber)' : 'var(--text-muted)'};">${priorityLabel}</span>
            </td>
            <td class="text-center">
                <div style="display: flex; gap: 4px; justify-content: center;">
                    <button class="btn-clear btn-edit" data-id="${task.id}" style="padding: 3px 6px; font-size: 11px;" title="Edit">Edit</button>
                    <button class="btn-clear btn-del" data-id="${task.id}" style="padding: 3px 6px; font-size: 11px; color: var(--status-red);" title="Delete">&times;</button>
                </div>
            </td>
        `;

        tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const taskId = e.currentTarget.dataset.id;
            loadTaskIntoForm(taskId);
        });
    });

    tbody.querySelectorAll('.btn-del').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const taskId = e.currentTarget.dataset.id;
            if (confirm('Delete this task entry?')) {
                await dataStore.deleteTask(taskId);
                showToast('Task deleted');
                refreshAll();
            }
        });
    });
}

function renderKanban(tasks) {
    const cols = {
        'in_progress': document.getElementById('kanban-list-in_progress'),
        'blocked': document.getElementById('kanban-list-blocked'),
        'review': document.getElementById('kanban-list-review'),
        'completed': document.getElementById('kanban-list-completed')
    };
    const counts = {
        'in_progress': document.getElementById('count-in_progress'),
        'blocked': document.getElementById('count-blocked'),
        'review': document.getElementById('count-review'),
        'completed': document.getElementById('count-completed')
    };

    for (const k in cols) {
        if (cols[k]) cols[k].innerHTML = '';
        if (counts[k]) counts[k].innerText = '0';
    }

    const colCounts = { in_progress: 0, blocked: 0, review: 0, completed: 0 };

    tasks.forEach(task => {
        const stKey = task.status || 'completed';
        colCounts[stKey] = (colCounts[stKey] || 0) + 1;
        const colList = cols[stKey] || cols['completed'];
        const member = state.members.find(m => m.id === task.memberId);

        const card = document.createElement('div');
        card.className = 'kanban-item-card';
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <strong>${member ? member.name : task.memberId}</strong>
                <span style="color: #3b82f6; font-weight: 700;">${(parseFloat(task.hours) || 0).toFixed(1)}h</span>
            </div>
            <div style="margin-bottom: 6px; color: #cbd5e1;">${escapeHTML(task.description)}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="cat-pill">${escapeHTML(task.category || 'General')}</span>
                ${task.thingsRequired ? `<span class="req-chip">Required</span>` : ''}
            </div>
        `;
        card.addEventListener('click', () => loadTaskIntoForm(task.id));
        if (colList) colList.appendChild(card);
    });

    for (const k in colCounts) {
        if (counts[k]) counts[k].innerText = colCounts[k];
    }
}

/* ==========================================================================
   POWERBI / TABLEAU LEVEL ANALYTICS ENGINE (CHART.JS)
   ========================================================================== */

function renderAnalyticsView(allTasks) {
    if (typeof Chart === 'undefined') return;

    const isDark = document.body.classList.contains('dark-theme');
    const textColor = isDark ? '#e8e8ec' : '#0a0a0a';
    const subColor = isDark ? '#9a9aaa' : '#716e85';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
    const fontFamily = "'Inter', -apple-system, sans-serif";

    // 1. Filter dataset according to timeframe & analyst filter
    const now = new Date();
    let filtered = [...allTasks];

    if (state.biTimeframe === 'today') {
        filtered = filtered.filter(t => t.date === state.activeDate);
    } else if (state.biTimeframe === '7days') {
        const d7 = new Date(now);
        d7.setDate(d7.getDate() - 7);
        const d7Str = getLocalDateStr(d7);
        filtered = filtered.filter(t => (t.date || '') >= d7Str);
    } else if (state.biTimeframe === '30days') {
        const d30 = new Date(now);
        d30.setDate(d30.getDate() - 30);
        const d30Str = getLocalDateStr(d30);
        filtered = filtered.filter(t => (t.date || '') >= d30Str);
    }

    if (state.biMember !== 'all') {
        filtered = filtered.filter(t => t.memberId === state.biMember);
    }

    // 2. Compute Top KPI Cards
    const totalHours = filtered.reduce((sum, t) => sum + (parseFloat(t.hours) || 0), 0);
    const billableHours = filtered.filter(t => !!t.isLabour).reduce((sum, t) => sum + (parseFloat(t.hours) || 0), 0);
    const billableRate = totalHours > 0 ? Math.round((billableHours / totalHours) * 100) : 0;
    
    const activeMemberIds = new Set(filtered.map(t => t.memberId));
    const activeCount = activeMemberIds.size;
    const avgHours = activeCount > 0 ? (totalHours / activeCount).toFixed(1) : '0.0';
    
    const reviewFlags = filtered.filter(t => !!t.isHighlighted).length;
    const onHoldCount = filtered.filter(t => t.status === 'blocked').length;

    const elTotalHours = document.getElementById('bi-kpi-total-hours');
    if (elTotalHours) elTotalHours.innerText = `${totalHours.toFixed(1)}h`;
    const elTasksCount = document.getElementById('bi-kpi-tasks-count');
    if (elTasksCount) elTasksCount.innerText = `${filtered.length} tasks recorded`;

    const elBillableRate = document.getElementById('bi-kpi-billable-rate');
    if (elBillableRate) elBillableRate.innerText = `${billableRate}%`;
    const elBillableHours = document.getElementById('bi-kpi-billable-hours');
    if (elBillableHours) elBillableHours.innerText = `${billableHours.toFixed(1)} billable hrs`;

    const elActiveAnalysts = document.getElementById('bi-kpi-active-analysts');
    if (elActiveAnalysts) elActiveAnalysts.innerText = state.biMember !== 'all' ? '1 Analyst' : `${activeCount} / 12`;
    const elAvgHours = document.getElementById('bi-kpi-avg-hours');
    if (elAvgHours) elAvgHours.innerText = `${avgHours}h avg / analyst`;

    const elReviewFlags = document.getElementById('bi-kpi-review-flags');
    if (elReviewFlags) elReviewFlags.innerText = reviewFlags;
    const elOnHoldCount = document.getElementById('bi-kpi-onhold-count');
    if (elOnHoldCount) elOnHoldCount.innerText = `${onHoldCount} on-hold items`;

    // 3. CHART 1: Charge Code & Discipline Allocation (Horizontal Bar)
    const catMap = {};
    filtered.forEach(t => {
        const cat = t.category || 'General Calculations';
        catMap[cat] = (catMap[cat] || 0) + (parseFloat(t.hours) || 0);
    });
    const sortedCats = Object.entries(catMap).sort((a, b) => b[1] - a[1]);
    const catLabels = sortedCats.map(c => c[0]);
    const catData = sortedCats.map(c => parseFloat(c[1].toFixed(1)));
    const catBadge = document.getElementById('bi-cat-total-badge');
    if (catBadge) catBadge.innerText = `${catLabels.length} Categories`;

    const ctx1 = document.getElementById('chart-charge-codes');
    if (ctx1) {
        if (biCharts.chargeCodes) biCharts.chargeCodes.destroy();
        biCharts.chargeCodes = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: catLabels.length > 0 ? catLabels : ['No Data'],
                datasets: [{
                    label: 'Logged Hours',
                    data: catData.length > 0 ? catData : [0],
                    backgroundColor: isDark ? 'rgba(96, 165, 250, 0.85)' : 'rgba(0, 20, 137, 0.85)',
                    borderColor: isDark ? '#60a5fa' : '#001489',
                    borderWidth: 1,
                    borderRadius: 0
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.parsed.x} hrs (${totalHours > 0 ? Math.round((ctx.parsed.x / totalHours) * 100) : 0}%)`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: subColor, font: { family: fontFamily, size: 11 } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: textColor, font: { family: fontFamily, size: 11, weight: '600' } }
                    }
                }
            }
        });
    }

    // 4. CHART 2: Team Member Workload & Billable Stacked Bar
    const ctx2 = document.getElementById('chart-team-workload');
    if (ctx2) {
        if (biCharts.teamWorkload) biCharts.teamWorkload.destroy();
        
        const memberList = state.biMember === 'all' 
            ? state.members 
            : state.members.filter(m => m.id === state.biMember);

        const mNames = memberList.map(m => m.name.split(' ')[0]);
        const billableByMem = memberList.map(m => {
            return filtered.filter(t => t.memberId === m.id && !!t.isLabour)
                .reduce((s, t) => s + (parseFloat(t.hours) || 0), 0);
        });
        const nonBillableByMem = memberList.map(m => {
            return filtered.filter(t => t.memberId === m.id && !t.isLabour)
                .reduce((s, t) => s + (parseFloat(t.hours) || 0), 0);
        });

        biCharts.teamWorkload = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: mNames,
                datasets: [
                    {
                        label: 'Billable Hours',
                        data: billableByMem,
                        backgroundColor: isDark ? '#60a5fa' : '#001489',
                        stack: 'hours'
                    },
                    {
                        label: 'Internal / Non-Billable',
                        data: nonBillableByMem,
                        backgroundColor: isDark ? '#3a3a48' : '#d8d8de',
                        stack: 'hours'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: textColor, font: { family: fontFamily, size: 11 }, boxWidth: 12 }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: { display: false },
                        ticks: { color: subColor, font: { family: fontFamily, size: 10 } }
                    },
                    y: {
                        stacked: true,
                        grid: { color: gridColor },
                        ticks: { color: subColor, font: { family: fontFamily, size: 11 } }
                    }
                },
                onClick: (evt, elements) => {
                    if (elements.length > 0) {
                        const idx = elements[0].index;
                        const clickedMem = memberList[idx];
                        if (clickedMem) {
                            state.drilldownMemberId = clickedMem.id;
                            renderIndividualDrilldown(allTasks);
                        }
                    }
                }
            }
        });
    }

    // 5. CHART 3: Daily Timeline Velocity Trend (Line / Area)
    const ctx3 = document.getElementById('chart-velocity-trend');
    if (ctx3) {
        if (biCharts.velocityTrend) biCharts.velocityTrend.destroy();

        const dateMap = {};
        filtered.forEach(t => {
            if (!t.date) return;
            dateMap[t.date] = (dateMap[t.date] || 0) + (parseFloat(t.hours) || 0);
        });
        const sortedDates = Object.keys(dateMap).sort();
        const dateValues = sortedDates.map(d => parseFloat(dateMap[d].toFixed(1)));

        biCharts.velocityTrend = new Chart(ctx3, {
            type: 'line',
            data: {
                labels: sortedDates.length > 0 ? sortedDates : ['No Dates'],
                datasets: [{
                    label: 'Daily Logged Hours',
                    data: dateValues.length > 0 ? dateValues : [0],
                    borderColor: isDark ? '#34d399' : '#1a7a4c',
                    backgroundColor: isDark ? 'rgba(52, 211, 153, 0.12)' : 'rgba(26, 122, 76, 0.10)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: isDark ? '#34d399' : '#1a7a4c'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: subColor, font: { family: fontFamily, size: 10 } }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: subColor, font: { family: fontFamily, size: 11 } }
                    }
                }
            }
        });
    }

    // 6. CHART 4: Operational Status & Priority Matrix (Doughnut)
    const ctx4 = document.getElementById('chart-status-priority');
    if (ctx4) {
        if (biCharts.statusPriority) biCharts.statusPriority.destroy();

        const statusCounts = {
            'Completed': filtered.filter(t => t.status === 'completed').length,
            'In Progress': filtered.filter(t => t.status === 'in_progress').length,
            'On Hold / Action Item': filtered.filter(t => t.status === 'blocked').length,
            'Under Review': filtered.filter(t => t.status === 'review').length
        };

        biCharts.statusPriority = new Chart(ctx4, {
            type: 'doughnut',
            data: {
                labels: Object.keys(statusCounts),
                datasets: [{
                    data: Object.values(statusCounts),
                    backgroundColor: [
                        isDark ? '#34d399' : '#1a7a4c',
                        isDark ? '#60a5fa' : '#001489',
                        isDark ? '#f87171' : '#b91c1c',
                        isDark ? '#fbbf24' : '#a16207'
                    ],
                    borderWidth: 2,
                    borderColor: isDark ? '#111118' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: textColor, font: { family: fontFamily, size: 11 }, boxWidth: 12 }
                    }
                }
            }
        });
    }

    // 7. Render Individual Analyst Drilldown
    renderIndividualDrilldown(allTasks);
}

function renderIndividualDrilldown(allTasks) {
    const memId = state.biMember !== 'all' ? state.biMember : state.drilldownMemberId;
    const member = state.members.find(m => m.id === memId) || state.members[0];
    if (!member) return;

    const mTasks = allTasks.filter(t => t.memberId === member.id);
    const totH = mTasks.reduce((s, t) => s + (parseFloat(t.hours) || 0), 0);
    const billableH = mTasks.filter(t => !!t.isLabour).reduce((s, t) => s + (parseFloat(t.hours) || 0), 0);

    const nameEl = document.getElementById('bi-analyst-name');
    if (nameEl) nameEl.innerText = member.name;
    const roleEl = document.getElementById('bi-analyst-role');
    if (roleEl) roleEl.innerText = `${member.role} • ${member.location}`;
    const avatarEl = document.getElementById('bi-analyst-avatar');
    if (avatarEl) {
        avatarEl.className = `avatar-large color-${(state.members.indexOf(member) % 8)}`;
        avatarEl.innerText = member.name.split(' ').map(n => n[0]).join('');
    }

    const totEl = document.getElementById('bi-analyst-total-hrs');
    if (totEl) totEl.innerText = `${totH.toFixed(1)}h`;
    const billEl = document.getElementById('bi-analyst-billable-hrs');
    if (billEl) billEl.innerText = `${billableH.toFixed(1)}h (${totH > 0 ? Math.round((billableH / totH) * 100) : 0}%)`;
    const countEl = document.getElementById('bi-analyst-task-count');
    if (countEl) countEl.innerText = mTasks.length;

    const tbody = document.getElementById('bi-analyst-tasks-tbody');
    if (tbody) {
        tbody.innerHTML = '';
        const sorted = [...mTasks].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
        if (sorted.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No tasks logged yet for ${escapeHTML(member.name)}.</td></tr>`;
            return;
        }

        sorted.forEach(t => {
            const tr = document.createElement('tr');
            const priority = t.priority || 'normal';
            const priorityLabel = priority.charAt(0).toUpperCase() + priority.slice(1);
            const statusLabel = t.status === 'blocked' ? 'On Hold' : t.status === 'review' ? 'Under Review' : t.status === 'in_progress' ? 'In Progress' : 'Completed';
            const statusClass = t.status || 'completed';

            tr.innerHTML = `
                <td><strong style="font-family: var(--font-mono); font-size: 12px;">${t.date || '-'}</strong></td>
                <td>
                    <div style="line-height: 1.35;">${escapeHTML(t.description)}</div>
                    ${t.isHighlighted ? '<span style="font-size: 10px; color: var(--status-amber); font-weight: 600;">[Management Review]</span> ' : ''}
                    ${t.isLabour ? '<span style="font-size: 10px; color: var(--status-blue); font-weight: 600;">[Billable]</span>' : ''}
                </td>
                <td><span class="cat-pill">${escapeHTML(t.category || 'General')}</span></td>
                <td><span style="font-size: 11px; font-family: var(--font-mono); color: var(--text-muted);">${escapeHTML(t.thingsRequired || '—')}</span></td>
                <td class="text-right"><strong>${(parseFloat(t.hours) || 0).toFixed(1)}h</strong></td>
                <td class="text-center">
                    <span style="font-size: 11px; text-transform: uppercase; font-weight: 600; color: ${priority === 'critical' ? 'var(--status-red)' : priority === 'high' ? 'var(--status-amber)' : 'var(--text-muted)'};">${priorityLabel}</span>
                </td>
                <td class="text-center"><span class="status-badge ${statusClass}">${statusLabel}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
}

function renderMLSection(allTasks, dayTasks) {
    // Compat stub
}

function renderTeamGrid(allTasks) {
    const grid = document.getElementById('team-roster-grid');
    grid.innerHTML = '';

    state.members.forEach(m => {
        const mTasks = allTasks.filter(t => t.memberId === m.id);
        const totH = mTasks.reduce((sum, t) => sum + (parseFloat(t.hours) || 0), 0);
        const dayTasks = mTasks.filter(t => t.date === state.activeDate);
        const dayH = dayTasks.reduce((sum, t) => sum + (parseFloat(t.hours) || 0), 0);

        const card = document.createElement('div');
        card.className = 'team-card';
        card.innerHTML = `
            <div class="team-card-head">
                ${getAvatarHTML(m, 'avatar-large')}
                <div class="team-card-info">
                    <h3>${m.name}</h3>
                    <p>${m.role} • ${m.location}</p>
                </div>
            </div>
            <div class="team-card-stats">
                <span>Today: <strong>${dayH.toFixed(1)}h</strong></span>
                <span>All-Time: <strong>${totH.toFixed(1)}h</strong></span>
                <span>Tasks: <strong>${mTasks.length}</strong></span>
            </div>
        `;

        card.querySelector('.avatar-large').addEventListener('click', (e) => {
            e.stopPropagation();
            window.targetUploadMemberId = m.id;
            document.getElementById('hidden-avatar-input').click();
        });

        card.addEventListener('click', () => {
            state.drilldownMemberId = m.id;
            state.biMember = m.id;
            const biMem = document.getElementById('bi-member-select');
            if (biMem) biMem.value = m.id;
            switchTab('analytics');
            dataStore.getAllTasks().then(all => renderAnalyticsView(all));
        });

        grid.appendChild(card);
    });
}

function renderTimesheet(allTasks) {
    const wrap = document.getElementById('timesheet-preview-area');
    const weekDates = getWeekDates(state.currentTimesheetMonday);
    const weekTasks = allTasks.filter(t => weekDates.includes(t.date));

    if (state.tsMemberFilter && state.tsMemberFilter !== 'all') {
        // Individual Analyst Detailed Weekly Timesheet View
        const member = state.members.find(m => m.id === state.tsMemberFilter) || state.members[0];
        const mTasks = weekTasks.filter(t => t.memberId === member.id);
        const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
        
        let html = `
            <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    ${getAvatarHTML(member, 'avatar-large')}
                    <div>
                        <h3 style="font-size: 16px; font-weight: 700;">${member.name}</h3>
                        <p style="font-size: 12px; color: var(--text-muted);">${member.role} • ${member.location}</p>
                    </div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button type="button" class="btn-submit-primary btn-ts-member-pdf" data-id="${member.id}">Download PDF</button>
                    <button type="button" class="btn-clear btn-ts-member-xlsx" data-id="${member.id}">Export Excel</button>
                </div>
            </div>
            <table class="simple-table">
                <thead>
                    <tr>
                        <th style="width: 110px;">Date</th>
                        <th style="width: 70px;">Day</th>
                        <th>Task Description</th>
                        <th style="width: 170px;">Charge Code</th>
                        <th style="width: 160px;">Work Order / Ref</th>
                        <th style="width: 70px;" class="text-right">Hours</th>
                        <th style="width: 80px;" class="text-center">Priority</th>
                        <th style="width: 100px;" class="text-center">Status</th>
                    </tr>
                </thead>
                <tbody>
        `;

        let totalWeeklyHours = 0;
        let totalBillableHours = 0;

        if (mTasks.length === 0) {
            html += `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No timesheet entries recorded for ${escapeHTML(member.name)} for this week.</td></tr>`;
        } else {
            mTasks.sort((a, b) => (a.date || '').localeCompare(b.date || ''));
            mTasks.forEach(t => {
                const dateObj = new Date(t.date + 'T00:00:00');
                const dayIdx = dateObj.getDay();
                const dayName = dayNames[dayIdx === 0 ? 4 : dayIdx - 1] || 'Day';
                const hrs = parseFloat(t.hours) || 0;
                totalWeeklyHours += hrs;
                if (t.isLabour) totalBillableHours += hrs;

                const priority = t.priority || 'normal';
                const priorityLabel = priority.charAt(0).toUpperCase() + priority.slice(1);
                const statusLabel = t.status === 'blocked' ? 'On Hold' : t.status === 'review' ? 'Under Review' : t.status === 'in_progress' ? 'In Progress' : 'Completed';
                const statusClass = t.status || 'completed';

                html += `
                    <tr>
                        <td><strong style="font-family: var(--font-mono); font-size: 12px;">${t.date}</strong></td>
                        <td style="color: var(--text-muted); font-size: 12px; font-weight: 600;">${dayName}</td>
                        <td>
                            <div style="line-height: 1.35;">${escapeHTML(t.description)}</div>
                            ${t.isHighlighted ? '<span style="font-size: 10px; color: var(--status-amber); font-weight: 600;">[Management Review]</span> ' : ''}
                            ${t.isLabour ? '<span style="font-size: 10px; color: var(--status-blue); font-weight: 600;">[Billable]</span>' : ''}
                        </td>
                        <td><span class="cat-pill">${escapeHTML(t.category || 'General')}</span></td>
                        <td><span style="font-size: 11px; font-family: var(--font-mono); color: var(--text-muted);">${escapeHTML(t.thingsRequired || '—')}</span></td>
                        <td class="text-right"><strong>${hrs.toFixed(1)}h</strong></td>
                        <td class="text-center">
                            <span style="font-size: 11px; text-transform: uppercase; font-weight: 600; color: ${priority === 'critical' ? 'var(--status-red)' : priority === 'high' ? 'var(--status-amber)' : 'var(--text-muted)'};">${priorityLabel}</span>
                        </td>
                        <td class="text-center"><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                    </tr>
                `;
            });
        }

        html += `
                </tbody>
                <tfoot>
                    <tr style="background: var(--bg-section); font-weight: 700;">
                        <td colspan="5">WEEKLY TOTAL (${totalBillableHours.toFixed(1)}h Billable)</td>
                        <td class="text-right" style="color: var(--status-blue); font-size: 15px;">${totalWeeklyHours.toFixed(1)}h</td>
                        <td colspan="2"></td>
                    </tr>
                </tfoot>
            </table>
        `;
        wrap.innerHTML = html;

        wrap.querySelectorAll('.btn-ts-member-pdf').forEach(btn => {
            btn.addEventListener('click', () => exportSingleMemberWeeklyPDF(btn.dataset.id, weekDates, allTasks));
        });
        wrap.querySelectorAll('.btn-ts-member-xlsx').forEach(btn => {
            btn.addEventListener('click', () => exportSingleMemberWeeklyXLSX(btn.dataset.id, weekDates, allTasks));
        });

    } else {
        // Entire Team Summary View
        let html = `
            <table class="simple-table">
                <thead>
                    <tr>
                        <th>Member</th>
                        <th>Role</th>
                        <th class="text-center">Mon</th>
                        <th class="text-center">Tue</th>
                        <th class="text-center">Wed</th>
                        <th class="text-center">Thu</th>
                        <th class="text-center">Fri</th>
                        <th class="text-right">Total Week</th>
                        <th class="text-center" style="width: 140px;">Download</th>
                    </tr>
                </thead>
                <tbody>
        `;

        state.members.forEach(m => {
            const mTasks = weekTasks.filter(t => t.memberId === m.id);
            const daily = [0, 0, 0, 0, 0];
            mTasks.forEach(t => {
                const idx = weekDates.indexOf(t.date);
                if (idx >= 0 && idx < 5) daily[idx] += parseFloat(t.hours) || 0;
            });
            const tot = daily.reduce((a, b) => a + b, 0);

            html += `
                <tr>
                    <td><strong>${m.name}</strong></td>
                    <td>${m.role}</td>
                    <td class="text-center">${daily[0] > 0 ? daily[0].toFixed(1) : '-'}</td>
                    <td class="text-center">${daily[1] > 0 ? daily[1].toFixed(1) : '-'}</td>
                    <td class="text-center">${daily[2] > 0 ? daily[2].toFixed(1) : '-'}</td>
                    <td class="text-center">${daily[3] > 0 ? daily[3].toFixed(1) : '-'}</td>
                    <td class="text-center">${daily[4] > 0 ? daily[4].toFixed(1) : '-'}</td>
                    <td class="text-right"><strong style="color: var(--status-blue);">${tot.toFixed(1)}h</strong></td>
                    <td class="text-center">
                        <button type="button" class="btn-clear btn-indiv-ts-pdf" data-id="${m.id}" style="padding: 3px 8px; font-size: 11px;" title="Download Individual PDF Timesheet">PDF</button>
                        <button type="button" class="btn-clear btn-indiv-ts-xlsx" data-id="${m.id}" style="padding: 3px 8px; font-size: 11px;" title="Download Individual Excel Timesheet">Excel</button>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        wrap.innerHTML = html;

        wrap.querySelectorAll('.btn-indiv-ts-pdf').forEach(btn => {
            btn.addEventListener('click', () => exportSingleMemberWeeklyPDF(btn.dataset.id, weekDates, allTasks));
        });
        wrap.querySelectorAll('.btn-indiv-ts-xlsx').forEach(btn => {
            btn.addEventListener('click', () => exportSingleMemberWeeklyXLSX(btn.dataset.id, weekDates, allTasks));
        });
    }
}

/* ==========================================================================
   DBMS PANEL RENDERING & CONTROLS
   ========================================================================== */

function renderDBMSView(allTasks) {
    // 1. Total records count
    const countEl = document.getElementById('dbms-total-records-count');
    if (countEl) countEl.innerText = allTasks.length;

    // 2. Engine status
    const engineEl = document.getElementById('dbms-engine-label');
    const syncBadge = document.getElementById('dbms-sync-badge');
    const headerStatus = document.getElementById('header-db-text');

    if (state.firebaseConnected) {
        if (engineEl) engineEl.innerText = "Google Firebase Realtime Database";
        if (syncBadge) syncBadge.innerHTML = "🟢 Cloud Realtime Active (Global Sync)";
        if (headerStatus) headerStatus.innerText = "Cloud Sync Active";
    } else {
        if (engineEl) engineEl.innerText = "Local REST Server (database.json)";
        if (syncBadge) syncBadge.innerHTML = "🟢 REST Server Active";
        if (headerStatus) headerStatus.innerText = "Local DB Active";
    }

    // 3. Raw records browser table
    const tbody = document.getElementById('dbms-raw-records-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const filterSearch = (state.dbmsSearchTerm || '').toLowerCase();
    const sorted = [...allTasks].sort((a, b) => (b.date || '').localeCompare(a.date || ''));

    const filtered = sorted.filter(t => {
        if (!filterSearch) return true;
        const mem = state.members.find(m => m.id === t.memberId)?.name || t.memberId;
        return (
            (t.id && t.id.toLowerCase().includes(filterSearch)) ||
            (t.description && t.description.toLowerCase().includes(filterSearch)) ||
            (t.category && t.category.toLowerCase().includes(filterSearch)) ||
            (t.thingsRequired && t.thingsRequired.toLowerCase().includes(filterSearch)) ||
            mem.toLowerCase().includes(filterSearch)
        );
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: #64748b; padding: 2rem;">No raw records match search criteria.</td></tr>`;
        return;
    }

    filtered.forEach(t => {
        const mem = state.members.find(m => m.id === t.memberId);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-family: var(--font-mono); font-size: 0.675rem; color: #64748b;">${t.id ? t.id.slice(0, 15) : '-'}</td>
            <td><strong>${mem ? mem.name : t.memberId}</strong></td>
            <td>${t.date || '-'}</td>
            <td style="line-height: 1.35;">${escapeHTML(t.description || '')}</td>
            <td><span class="cat-pill">${escapeHTML(t.category || 'General')}</span></td>
            <td><span style="font-size: 0.725rem; color: #c4b5fd;">${escapeHTML(t.thingsRequired || '-')}</span></td>
            <td class="text-right"><strong>${(parseFloat(t.hours) || 0).toFixed(1)}h</strong></td>
            <td class="text-center"><span class="status-badge ${t.status || 'completed'}">${t.status || 'completed'}</span></td>
            <td class="text-center">
                <button class="btn-clear btn-edit" data-id="${t.id}" style="padding: 3px 8px; font-size: 11px;" title="Edit">Edit</button>
                <button class="btn-clear btn-del" data-id="${t.id}" style="padding: 3px 8px; font-size: 11px; color: var(--status-red);" title="Delete">Del</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            loadTaskIntoForm(e.currentTarget.dataset.id);
            switchTab('feed');
        });
    });

    tbody.querySelectorAll('.btn-del').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const taskId = e.currentTarget.dataset.id;
            if (confirm('Permanently delete this record from the database?')) {
                await dataStore.deleteTask(taskId);
                showToast('Record deleted from database');
                refreshAll();
            }
        });
    });
}

function exportDatabaseJSON() {
    const data = {
        app: "Chevron Operations & Daily Tracker",
        version: "2.0",
        exportedAt: new Date().toISOString(),
        membersCount: state.members.length,
        tasksCount: state.allTasksCache.length,
        members: state.members,
        tasks: state.allTasksCache
    };

    const str = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", str);
    downloadAnchor.setAttribute("download", `chevron_database_backup_${new Date().toISOString().split('T')[0]}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();

    showToast('Database backup downloaded successfully (.json)');
}

/* ==========================================================================
   FORM & ACTION CONTROLS
   ========================================================================== */

function populateMemberDropdowns() {
    const fSelect = document.getElementById('form-member-id');
    const filterSelect = document.getElementById('db-filter-member');
    const biSelect = document.getElementById('bi-member-select');

    if (fSelect) fSelect.innerHTML = '';
    if (filterSelect) filterSelect.innerHTML = '<option value="all">All Members</option>';
    if (biSelect) biSelect.innerHTML = '<option value="all">Entire Team (12 Members)</option>';

    state.members.forEach(m => {
        if (fSelect) {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = `${m.name} (${m.role})`;
            fSelect.appendChild(opt);
        }

        if (filterSelect) {
            const filterOpt = document.createElement('option');
            filterOpt.value = m.id;
            filterOpt.textContent = m.name;
            filterSelect.appendChild(filterOpt);
        }

        if (biSelect) {
            const biOpt = document.createElement('option');
            biOpt.value = m.id;
            biOpt.textContent = `${m.name} (${m.location})`;
            biSelect.appendChild(biOpt);
        }
    });
}

function createTaskRowHTML(idx, data = {}) {
    const desc = data.description ? escapeHTML(data.description) : '';
    const assets = data.assets || data.thingsRequired || '';
    const hours = (data.hours !== undefined && data.hours !== null) ? data.hours : '';
    const metric = (data.metricHours !== undefined && data.metricHours !== null && data.metricHours !== '') ? data.metricHours : '0.25';
    const count = (data.countPerDay !== undefined && data.countPerDay !== null && data.countPerDay !== '') ? data.countPerDay : '';
    const achieved = (data.achievedOnDay !== undefined && data.achievedOnDay !== null && data.achievedOnDay !== '') ? data.achievedOnDay : '';
    let eff = data.efficiency || '';
    let effNum = null;
    let targetNum = (count !== undefined && count !== null && count !== '') ? parseFloat(count) : 0;
    const hoursNum = parseFloat(hours) || 0;
    const metricNum = parseFloat(metric) || 0.25;
    if (targetNum <= 0 && hoursNum > 0 && metricNum > 0) {
        targetNum = Math.round(hoursNum / metricNum);
    }
    const achNum = (achieved !== undefined && achieved !== null && achieved !== '') ? parseFloat(achieved) : null;
    if (targetNum > 0 && achNum !== null && !isNaN(achNum)) {
        effNum = Math.round((achNum / targetNum) * 100);
        eff = `${effNum}%`;
    } else if (eff && eff.includes('%')) {
        effNum = parseInt(eff);
    }
    const effClass = (effNum !== null && effNum >= 80) ? 'eff-badge-high' : (effNum !== null && effNum >= 50) ? 'eff-badge-mid' : (effNum !== null ? 'eff-badge-low' : 'eff-badge-none');
    const roadblocks = data.roadblocks ? escapeHTML(data.roadblocks) : '';
    const notes = data.notes ? escapeHTML(data.notes) : '';
    const category = data.category ? escapeHTML(data.category) : '';

    return `
    <div class="task-row" data-row="${idx}">
        <div class="task-row-top">
            <div class="form-group flex-task-desc">
                <label>Task Description <span class="req">*</span></label>
                <input type="text" class="simple-input task-desc-input" value="${desc}" placeholder="What did you work on?" required>
            </div>
            <div class="form-group flex-task-assets">
                <label>Assets / Units / ISOs / PIDs</label>
                <input type="text" class="simple-input task-assets-input" value="${escapeHTML(assets)}" placeholder="e.g. Tank X-3109, ISO-48291">
            </div>
            <div class="form-group w-hrs">
                <label>Hrs/day <span class="req">*</span></label>
                <input type="number" class="simple-input task-hours-input" step="0.25" min="0" max="24" value="${hours}" placeholder="0" required>
            </div>
            <div class="form-group w-metric">
                <label title="metric/task in hrs">Metric (hrs)</label>
                <input type="number" class="simple-input task-metric-input" step="0.05" min="0" max="24" value="${metric}" placeholder="0.25">
            </div>
            <div class="form-group w-count">
                <label title="count per day (target)">Target Count</label>
                <input type="number" class="simple-input task-count-input" step="1" min="0" value="${count}" placeholder="${targetNum > 0 ? targetNum : 10}">
            </div>
            <div class="form-group w-achieved">
                <label title="achieved on the day">Achieved</label>
                <input type="number" class="simple-input task-achieved-input" step="1" min="0" value="${achieved}" placeholder="6">
            </div>
            <div class="form-group w-efficiency">
                <label title="Calculated as Achieved / Target Count">Efficiency</label>
                <div class="task-efficiency-badge ${effClass}" title="Auto-calculated (Achieved / Target Count)">${eff || '—'}</div>
                <input type="hidden" class="task-efficiency-input" value="${eff}">
            </div>
            <button type="button" class="btn-remove-row" title="Remove or clear this row">&times;</button>
        </div>
        <div class="task-row-bottom">
            <div class="form-group flex-roadblocks">
                <label>Road blocks</label>
                <input type="text" class="simple-input task-roadblocks-input" value="${roadblocks}" placeholder="Any blockers, missing info, or impediments...">
            </div>
            <div class="form-group flex-notes">
                <label>Notes</label>
                <input type="text" class="simple-input task-notes-input" value="${notes}" placeholder="Specific notes, revisions, or comments...">
            </div>
            <div class="form-group flex-category">
                <label>Charge Code / Category</label>
                <input type="text" class="simple-input task-category-input" list="charge-code-list" value="${category}" placeholder="Type or select">
            </div>
        </div>
    </div>`;
}

function updateRowEfficiency(row) {
    if (!row) return;
    const countInput = row.querySelector('.task-count-input');
    const achInput = row.querySelector('.task-achieved-input');
    const hoursInput = row.querySelector('.task-hours-input');
    const metricInput = row.querySelector('.task-metric-input');
    const badge = row.querySelector('.task-efficiency-badge');
    const hidden = row.querySelector('.task-efficiency-input');
    if (!badge) return;

    let count = parseFloat(countInput?.value);
    const ach = parseFloat(achInput?.value);
    const hours = parseFloat(hoursInput?.value);
    const metric = parseFloat(metricInput?.value);

    // If count not explicitly entered, but hours & metric are: auto-suggest target
    if ((isNaN(count) || count <= 0) && !isNaN(hours) && hours > 0 && !isNaN(metric) && metric > 0) {
        count = Math.round(hours / metric);
        if (countInput && !countInput.value) {
            countInput.placeholder = count;
        }
    }

    if (!isNaN(count) && count > 0 && !isNaN(ach)) {
        const pct = Math.round((ach / count) * 100);
        badge.innerText = `${pct}%`;
        if (hidden) hidden.value = `${pct}%`;
        badge.className = 'task-efficiency-badge ' + (pct >= 80 ? 'eff-badge-high' : pct >= 50 ? 'eff-badge-mid' : 'eff-badge-low');
    } else {
        badge.innerText = '—';
        if (hidden) hidden.value = '';
        badge.className = 'task-efficiency-badge eff-badge-none';
    }
}

function clearTaskForm() {
    document.getElementById('form-task-id').value = '';
    document.getElementById('form-things-required').value = '';
    document.getElementById('form-status').value = 'completed';
    document.getElementById('form-is-highlighted').checked = false;
    document.getElementById('form-is-labour').checked = false;
    const priorityEl = document.getElementById('form-priority');
    if (priorityEl) priorityEl.value = 'normal';
    document.getElementById('btn-submit-task').innerHTML = '<span>Submit Entry</span>';
    
    // Hide Delete Task button in creation mode
    const delBtn = document.getElementById('btn-delete-current-task');
    if (delBtn) delBtn.style.display = 'none';

    // Reset multi-task rows to one clean template row
    const container = document.getElementById('task-rows-container');
    if (container) {
        container.innerHTML = createTaskRowHTML(0);
        updateRemoveButtons();
    }
    document.getElementById('form-description').value = '';
    document.getElementById('form-hours').value = '';
    try { document.getElementById('form-ml-tag-preview').innerText = ''; } catch(e) {}
}

async function loadTaskIntoForm(taskId) {
    const allTasks = await dataStore.getAllTasks();
    const task = allTasks.find(t => t.id === taskId);
    if (!task) return;

    document.getElementById('form-task-id').value = task.id;
    document.getElementById('form-member-id').value = task.memberId;
    document.getElementById('form-things-required').value = task.assets || task.thingsRequired || '';
    document.getElementById('form-status').value = task.status || 'completed';
    document.getElementById('form-is-highlighted').checked = !!task.isHighlighted;
    document.getElementById('form-is-labour').checked = !!task.isLabour;
    const priorityEl = document.getElementById('form-priority');
    if (priorityEl) priorityEl.value = task.priority || 'normal';
    document.getElementById('btn-submit-task').innerHTML = '<span>Update Entry</span>';

    // Show Delete Task button in editing mode
    const delBtn = document.getElementById('btn-delete-current-task');
    if (delBtn) {
        delBtn.style.display = 'inline-block';
        delBtn.onclick = async () => {
            if (confirm(`Permanently delete this task entry? ("${task.description.substring(0, 35)}...")`)) {
                await dataStore.deleteTask(taskId);
                clearTaskForm();
                showToast('Task permanently removed');
                refreshAll();
            }
        };
    }

    // Populate multi-task row with this task's full production metrics
    const container = document.getElementById('task-rows-container');
    if (container) {
        container.innerHTML = createTaskRowHTML(0, task);
        const rowEl = container.querySelector('.task-row');
        if (rowEl) updateRowEfficiency(rowEl);
        updateRemoveButtons();
    }

    // Set hidden legacy fields
    document.getElementById('form-description').value = task.description;
    document.getElementById('form-hours').value = task.hours;

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ==========================================================================
   INITIALIZATION & EVENT BINDINGS
   ========================================================================== */

async function refreshAll() {
    state.tasks = await dataStore.getTasks(state.activeDate);
    const allTasks = await dataStore.getAllTasks();

    updateSummaryKPIs(state.tasks);
    renderExcelMemberTabs(state.tasks);
    renderFeedTable(state.tasks);
    renderKanban(state.tasks);
    renderAnalyticsView(allTasks);
    renderTeamGrid(allTasks);
    renderTimesheet(allTasks);
    renderDBMSView(allTasks);
}

function switchTab(tabId) {
    state.activeTab = tabId;
    document.querySelectorAll('.pill-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    document.querySelectorAll('.view-panel').forEach(p => {
        p.classList.toggle('active', p.id === `panel-${tabId}`);
    });
    if (tabId === 'analytics') {
        // Automatically sync to currently active member if available
        if (state.currentUserMemberId) {
            state.biMember = state.currentUserMemberId;
            state.drilldownMemberId = state.currentUserMemberId;
            const biSelect = document.getElementById('bi-member-select');
            if (biSelect) biSelect.value = state.currentUserMemberId;
        }
        dataStore.getAllTasks().then(all => renderAnalyticsView(all));
    }
    if (tabId === 'timesheet') {
        dataStore.getAllTasks().then(all => renderTimesheet(all));
    }
}

function setupListeners() {
    // Tabs
    document.querySelectorAll('.pill-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Form Member Selector — User awareness
    const fMemSelect = document.getElementById('form-member-id');
    if (fMemSelect) {
        fMemSelect.addEventListener('change', (e) => {
            const mId = e.target.value;
            state.currentUserMemberId = mId;
            state.drilldownMemberId = mId;
            state.biMember = mId;
            const biSelect = document.getElementById('bi-member-select');
            if (biSelect) biSelect.value = mId;
        });
    }

    // BI Controls
    const biTimeSelect = document.getElementById('bi-timeframe-select');
    if (biTimeSelect) {
        biTimeSelect.addEventListener('change', async (e) => {
            state.biTimeframe = e.target.value;
            const all = await dataStore.getAllTasks();
            renderAnalyticsView(all);
        });
    }

    const biMemSelect = document.getElementById('bi-member-select');
    if (biMemSelect) {
        biMemSelect.addEventListener('change', async (e) => {
            state.biMember = e.target.value;
            if (state.biMember !== 'all') {
                state.drilldownMemberId = state.biMember;
                state.currentUserMemberId = state.biMember;
            }
            const all = await dataStore.getAllTasks();
            renderAnalyticsView(all);
        });
    }

    // Timesheet Member Filter
    const tsFilterSelect = document.getElementById('ts-member-filter');
    if (tsFilterSelect) {
        tsFilterSelect.addEventListener('change', async (e) => {
            state.tsMemberFilter = e.target.value;
            const all = await dataStore.getAllTasks();
            renderTimesheet(all);
        });
    }

    // Header Export Today's Excel Button
    const btnExportToday = document.getElementById('btn-export-today-xlsx');
    if (btnExportToday) {
        btnExportToday.addEventListener('click', exportTodayTasksXLSX);
    }

    // Date Navigation
    const dInput = document.getElementById('tracker-date');
    dInput.value = state.activeDate;
    dInput.addEventListener('change', (e) => {
        state.activeDate = e.target.value;
        refreshAll();
    });

    document.getElementById('btn-prev-day').addEventListener('click', () => {
        const d = new Date(state.activeDate + 'T00:00:00');
        d.setDate(d.getDate() - 1);
        state.activeDate = getLocalDateStr(d);
        dInput.value = state.activeDate;
        refreshAll();
    });

    document.getElementById('btn-next-day').addEventListener('click', () => {
        const d = new Date(state.activeDate + 'T00:00:00');
        d.setDate(d.getDate() + 1);
        state.activeDate = getLocalDateStr(d);
        dInput.value = state.activeDate;
        refreshAll();
    });

    document.getElementById('btn-today-shortcut').addEventListener('click', () => {
        state.activeDate = getLocalDateStr(new Date());
        dInput.value = state.activeDate;
        refreshAll();
    });

    // Live ML classification on typing (legacy — disabled, kept for compat)
    const desc = document.getElementById('form-description');
    // No-op: ML auto-classify removed for corporate simplicity

    // Submit form — handles MULTIPLE task rows
    document.getElementById('inline-task-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const editId = document.getElementById('form-task-id').value;
        const memberId = document.getElementById('form-member-id').value;
        const status = document.getElementById('form-status').value;
        const thingsRequired = document.getElementById('form-things-required').value;
        const isHighlighted = document.getElementById('form-is-highlighted').checked;
        const isLabour = document.getElementById('form-is-labour').checked;
        const priorityEl = document.getElementById('form-priority');
        const priority = priorityEl ? priorityEl.value : 'normal';

        // Keep current user awareness
        state.currentUserMemberId = memberId;
        state.drilldownMemberId = memberId;
        state.biMember = memberId;
        const biSelect = document.getElementById('bi-member-select');
        if (biSelect) biSelect.value = memberId;

        // Gather all task rows
        const rows = document.querySelectorAll('#task-rows-container .task-row');
        const tasksToSave = [];

        rows.forEach((row, idx) => {
            const descInput = row.querySelector('.task-desc-input');
            const assetsInput = row.querySelector('.task-assets-input');
            const hoursInput = row.querySelector('.task-hours-input');
            const metricInput = row.querySelector('.task-metric-input');
            const countInput = row.querySelector('.task-count-input');
            const achievedInput = row.querySelector('.task-achieved-input');
            const effInput = row.querySelector('.task-efficiency-input');
            const roadblocksInput = row.querySelector('.task-roadblocks-input');
            const notesInput = row.querySelector('.task-notes-input');
            const catInput = row.querySelector('.task-category-input');

            if (!descInput || !descInput.value.trim()) return;

            const text = descInput.value.trim();
            const rowAssets = (assetsInput && assetsInput.value.trim()) ? assetsInput.value.trim() : (thingsRequired || '');
            const rowHours = parseFloat(hoursInput.value) || 0;
            const rowMetric = (metricInput && metricInput.value !== '') ? parseFloat(metricInput.value) : 0.25;
            const rowCount = (countInput && countInput.value !== '') ? parseFloat(countInput.value) : null;
            const rowAchieved = (achievedInput && achievedInput.value !== '') ? parseFloat(achievedInput.value) : null;
            
            let rowEff = (effInput && effInput.value) ? effInput.value : '';
            if (!rowEff && rowCount > 0 && rowAchieved !== null) {
                rowEff = Math.round((rowAchieved / rowCount) * 100) + '%';
            }

            const rowRoadblocks = roadblocksInput ? roadblocksInput.value.trim() : '';
            const rowNotes = notesInput ? notesInput.value.trim() : '';
            const ml = MLEngine.classifyTask(text);

            tasksToSave.push({
                id: (idx === 0 && editId) ? editId : undefined,
                memberId,
                date: state.activeDate,
                description: text,
                hours: rowHours,
                assets: rowAssets,
                thingsRequired: rowAssets, // preserve backward compatibility
                metricHours: rowMetric,
                countPerDay: rowCount,
                achievedOnDay: rowAchieved,
                efficiency: rowEff,
                roadblocks: rowRoadblocks,
                notes: rowNotes,
                category: (catInput && catInput.value.trim()) ? catInput.value.trim() : ml.category,
                status,
                isHighlighted,
                isLabour,
                priority,
                complexityScore: ml.complexity,
                confidenceScore: ml.confidence
            });
        });

        if (tasksToSave.length === 0) {
            showToast('Please enter at least one task');
            return;
        }

        // Save all tasks
        for (const taskData of tasksToSave) {
            await dataStore.saveTask(taskData);
        }

        clearTaskForm();
        const msg = tasksToSave.length === 1
            ? (editId ? 'Task updated' : 'Task submitted')
            : `${tasksToSave.length} tasks submitted`;
        showToast(msg);
        refreshAll();
    });

    document.getElementById('btn-clear-form').addEventListener('click', clearTaskForm);

    // Multi-task row: Add row
    document.getElementById('btn-add-task-row').addEventListener('click', () => {
        const container = document.getElementById('task-rows-container');
        const rowCount = container.querySelectorAll('.task-row').length;
        const temp = document.createElement('div');
        temp.innerHTML = createTaskRowHTML(rowCount);
        const newRow = temp.firstElementChild;
        container.appendChild(newRow);
        updateRemoveButtons();
        newRow.querySelector('.task-desc-input')?.focus();
    });

    // Multi-task row: Live efficiency calculation on input
    document.getElementById('task-rows-container').addEventListener('input', (e) => {
        if (
            e.target.classList.contains('task-count-input') ||
            e.target.classList.contains('task-achieved-input') ||
            e.target.classList.contains('task-hours-input') ||
            e.target.classList.contains('task-metric-input')
        ) {
            updateRowEfficiency(e.target.closest('.task-row'));
        }
    });

    // Multi-task row: Remove or clear row (delegated)
    document.getElementById('task-rows-container').addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-remove-row');
        if (btn) {
            const row = btn.closest('.task-row');
            const allRows = document.querySelectorAll('#task-rows-container .task-row');
            if (allRows.length > 1) {
                if (row) row.remove();
                updateRemoveButtons();
                showToast('Task row removed');
            } else if (row) {
                // If single row, clear all inputs to reset cleanly
                row.querySelectorAll('input').forEach(inp => {
                    if (inp.classList.contains('task-metric-input')) inp.value = '0.25';
                    else if (inp.type !== 'button' && inp.type !== 'submit') inp.value = '';
                });
                updateRowEfficiency(row);
                showToast('Task row cleared');
            }
        }
    });

    // Theme toggle
    const themeBtn = document.getElementById('btn-theme-toggle');
    if (themeBtn) {
        // Restore saved theme
        const saved = localStorage.getItem('chevron-theme');
        if (saved === 'dark') {
            document.body.classList.add('dark-theme');
            document.getElementById('theme-icon').innerHTML = '&#9788;'; // sun
        }
        themeBtn.addEventListener('click', async () => {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            document.getElementById('theme-icon').innerHTML = isDark ? '&#9788;' : '&#9789;';
            localStorage.setItem('chevron-theme', isDark ? 'dark' : 'light');
            const all = await dataStore.getAllTasks();
            renderAnalyticsView(all);
        });
    }

    // Search & Filters
    document.getElementById('db-search-input').addEventListener('input', (e) => {
        state.searchTerm = e.target.value;
        renderFeedTable(state.tasks);
    });

    document.getElementById('db-filter-member').addEventListener('change', (e) => {
        state.filterMember = e.target.value;
        updateSummaryKPIs(state.tasks);
        renderExcelMemberTabs(state.tasks);
        renderFeedTable(state.tasks);
    });

    document.getElementById('db-filter-status').addEventListener('change', (e) => {
        state.filterStatus = e.target.value;
        renderFeedTable(state.tasks);
    });

    // DBMS Controls
    document.getElementById('btn-dbms-export-json').addEventListener('click', exportDatabaseJSON);

    document.getElementById('btn-dbms-trigger-import').addEventListener('click', () => {
        document.getElementById('dbms-import-file-input').click();
    });

    document.getElementById('dbms-import-file-input').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async (evt) => {
            try {
                const json = JSON.parse(evt.target.result);
                const res = await dataStore.importFullDatabase(json);
                showToast(`Database restored (${res.members} members, ${res.tasks} tasks)`);
                refreshAll();
            } catch (err) {
                alert('Failed to import: ' + err.message);
            }
        };
        reader.readAsText(file);
    });

    document.getElementById('btn-dbms-seed').addEventListener('click', async () => {
        if (confirm('Reset and seed database with the 12 Chevron Reliability Analysts?')) {
            await dataStore.resetDatabaseToDefault();
            showToast('Database reset to default team data');
            refreshAll();
        }
    });

    document.getElementById('dbms-search-input').addEventListener('input', (e) => {
        state.dbmsSearchTerm = e.target.value;
        renderDBMSView(state.allTasksCache);
    });

    // Standup modal (hidden but wired for compat)
    document.getElementById('btn-open-ai-standup').addEventListener('click', () => {});
    document.getElementById('btn-close-standup-modal').addEventListener('click', () => {
        document.getElementById('standup-modal').classList.remove('active');
    });
    document.getElementById('standup-format-style').addEventListener('change', () => {});
    document.getElementById('btn-copy-standup').addEventListener('click', () => {});

    // Avatar upload
    document.getElementById('hidden-avatar-input').addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file || !window.targetUploadMemberId) return;
        const formData = new FormData();
        formData.append('avatar', file);
        await fetch(`/api/members/${window.targetUploadMemberId}/avatar`, { method: 'POST', body: formData });
        showToast('Avatar updated');
        await dataStore.loadMembers();
        refreshAll();
    });

    // Timesheet Prev / Next
    document.getElementById('btn-ts-prev-week').addEventListener('click', () => {
        state.currentTimesheetMonday.setDate(state.currentTimesheetMonday.getDate() - 7);
        updateTsLabel();
        dataStore.getAllTasks().then(all => renderTimesheet(all));
    });

    document.getElementById('btn-ts-next-week').addEventListener('click', () => {
        state.currentTimesheetMonday.setDate(state.currentTimesheetMonday.getDate() + 7);
        updateTsLabel();
        dataStore.getAllTasks().then(all => renderTimesheet(all));
    });

    document.getElementById('btn-export-timesheet-xlsx').addEventListener('click', exportTimesheetXLSX);
    document.getElementById('btn-generate-timesheet-pdf').addEventListener('click', exportTimesheetPDF);
}

function updateTsLabel() {
    const dates = getWeekDates(state.currentTimesheetMonday);
    document.getElementById('timesheet-week-label').innerText = `Week of ${dates[0]} — ${dates[4]}`;
}

function getLocalDateStr(d) {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function getMonday(d) {
    const date = new Date(d);
    const day = date.getDay();
    return new Date(date.setDate(date.getDate() - day + (day === 0 ? -6 : 1)));
}

function getWeekDates(monday) {
    const dates = [];
    for (let i = 0; i < 5; i++) {
        const d = new Date(monday);
        d.setDate(d.getDate() + i);
        dates.push(getLocalDateStr(d));
    }
    return dates;
}

function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function updateRemoveButtons() {
    const container = document.getElementById('task-rows-container');
    if (!container) return;
    const rows = container.querySelectorAll('.task-row');
    rows.forEach(row => {
        const btn = row.querySelector('.btn-remove-row');
        if (btn) {
            btn.style.visibility = 'visible';
            btn.title = rows.length > 1 ? 'Remove this task row' : 'Clear this row';
        }
    });
}

function showToast(msg) {
    const c = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = 'toast';
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => t.remove(), 2800);
}

/* ==========================================================================
   LIVE EXPORT ENGINES (EXCEL & PDF)
   ========================================================================== */

async function exportTodayTasksXLSX() {
    if (typeof XLSX === 'undefined') return alert('Loading Excel library, please retry in a second...');
    const dayTasks = await dataStore.getTasks(state.activeDate);
    if (dayTasks.length === 0) {
        return alert(`No tasks logged for today (${state.activeDate}) to export.`);
    }

    function formatTaskForExcel(t, idx) {
        const member = state.members.find(m => m.id === t.memberId);
        const workerName = member ? member.name : t.memberId;
        const target = (t.countPerDay !== undefined && t.countPerDay !== null && t.countPerDay !== '') ? parseFloat(t.countPerDay) : '';
        const achieved = (t.achievedOnDay !== undefined && t.achievedOnDay !== null && t.achievedOnDay !== '') ? parseFloat(t.achievedOnDay) : '';
        let eff = t.efficiency || '';
        if (!eff && target > 0 && achieved !== '') {
            eff = `${Math.round((achieved / target) * 100)}%`;
        }

        return {
            "S.No": idx + 1,
            "Date": t.date || state.activeDate,
            "Task worker": workerName,
            "Task": t.description || '',
            "Assets/Units/ISOs/PIDs": t.assets || t.thingsRequired || '',
            "Hrs/day": parseFloat(t.hours) || 0,
            "metric/task in hrs": (t.metricHours !== undefined && t.metricHours !== null && t.metricHours !== '') ? parseFloat(t.metricHours) : 0.25,
            "count per day": target,
            "achieved on the day": achieved,
            "Efficiency": eff,
            "Road blocks": t.roadblocks || '',
            "Notes": t.notes || '',
            "Charge Code / Category": t.category || 'General',
            "Priority": (t.priority || 'normal').toUpperCase(),
            "Status": (t.status || 'completed').toUpperCase(),
            "Management Review": t.isHighlighted ? 'YES' : 'NO',
            "Billable": t.isLabour ? 'YES' : 'NO'
        };
    }

    const masterRows = dayTasks.map((t, idx) => formatTaskForExcel(t, idx));
    const totalHours = dayTasks.reduce((sum, t) => sum + (parseFloat(t.hours) || 0), 0);
    const totalTarget = dayTasks.reduce((sum, t) => sum + (parseFloat(t.countPerDay) || 0), 0);
    const totalAchieved = dayTasks.reduce((sum, t) => sum + (parseFloat(t.achievedOnDay) || 0), 0);

    masterRows.push({
        "S.No": "",
        "Date": "TOTAL",
        "Task worker": `${dayTasks.length} Tasks Logged`,
        "Task": "",
        "Assets/Units/ISOs/PIDs": "",
        "Hrs/day": totalHours,
        "metric/task in hrs": "",
        "count per day": totalTarget > 0 ? totalTarget : "",
        "achieved on the day": totalAchieved > 0 ? totalAchieved : "",
        "Efficiency": totalTarget > 0 ? `${Math.round((totalAchieved / totalTarget) * 100)}%` : "",
        "Road blocks": "",
        "Notes": "",
        "Charge Code / Category": "",
        "Priority": "",
        "Status": "",
        "Management Review": "",
        "Billable": ""
    });

    const wb = XLSX.utils.book_new();
    const wsMaster = XLSX.utils.json_to_sheet(masterRows);
    XLSX.utils.book_append_sheet(wb, wsMaster, "Master Log");

    // Add individual sheets for each team member matching the screenshot tabs
    state.members.forEach(m => {
        const shortName = getMemberShortName(m);
        const mTasks = dayTasks.filter(t => t.memberId === m.id);
        let mRows = [];
        if (mTasks.length > 0) {
            mRows = mTasks.map((t, i) => formatTaskForExcel(t, i));
            const mTotH = mTasks.reduce((sum, t) => sum + (parseFloat(t.hours) || 0), 0);
            mRows.push({
                "S.No": "",
                "Date": "TOTAL",
                "Task worker": m.name,
                "Task": `${mTasks.length} Tasks`,
                "Assets/Units/ISOs/PIDs": "",
                "Hrs/day": mTotH,
                "metric/task in hrs": "",
                "count per day": "",
                "achieved on the day": "",
                "Efficiency": "",
                "Road blocks": "",
                "Notes": "",
                "Charge Code / Category": "",
                "Priority": "",
                "Status": "",
                "Management Review": "",
                "Billable": ""
            });
        } else {
            // Template row if no entries today
            mRows.push({
                "S.No": 1,
                "Date": state.activeDate,
                "Task worker": m.name,
                "Task": "",
                "Assets/Units/ISOs/PIDs": "",
                "Hrs/day": "",
                "metric/task in hrs": 0.25,
                "count per day": "",
                "achieved on the day": "",
                "Efficiency": "",
                "Road blocks": "",
                "Notes": "",
                "Charge Code / Category": "",
                "Priority": "",
                "Status": "",
                "Management Review": "",
                "Billable": ""
            });
        }
        const wsMember = XLSX.utils.json_to_sheet(mRows);
        XLSX.utils.book_append_sheet(wb, wsMember, shortName.slice(0, 31));
    });

    XLSX.writeFile(wb, `Chevron_Daily_Production_Tracker_${state.activeDate}.xlsx`);
    showToast(`Exported ${dayTasks.length} entries for ${state.activeDate} with member sheets to Excel`);
}

async function exportSingleMemberWeeklyXLSX(memberId, weekDates, allTasks) {
    if (typeof XLSX === 'undefined') return alert('Loading Excel...');
    const member = state.members.find(m => m.id === memberId) || { name: memberId, role: 'Analyst' };
    const tasks = (allTasks || await dataStore.getAllTasks()).filter(t => t.memberId === memberId && weekDates.includes(t.date));

    const rows = tasks.map((t, idx) => ({
        "S.No": idx + 1,
        "Date": t.date,
        "Task worker": member.name,
        "Task": t.description,
        "Assets/Units/ISOs/PIDs": t.assets || t.thingsRequired || '',
        "Hrs/day": parseFloat(t.hours) || 0,
        "metric/task in hrs": t.metricHours || 0.25,
        "count per day": t.countPerDay || '',
        "achieved on the day": t.achievedOnDay || '',
        "Efficiency": t.efficiency || '',
        "Road blocks": t.roadblocks || '',
        "Notes": t.notes || '',
        "Charge Code": t.category || 'General',
        "Priority": (t.priority || 'normal').toUpperCase(),
        "Status": (t.status || 'completed').toUpperCase(),
        "Billable": t.isLabour ? 'YES' : 'NO'
    }));

    const totH = tasks.reduce((s, t) => s + (parseFloat(t.hours) || 0), 0);
    rows.push({
        "S.No": "",
        "Date": "WEEKLY TOTAL",
        "Task worker": member.name,
        "Task": `${tasks.length} tasks`,
        "Assets/Units/ISOs/PIDs": "",
        "Hrs/day": totH,
        "metric/task in hrs": "",
        "count per day": "",
        "achieved on the day": "",
        "Efficiency": "",
        "Road blocks": "",
        "Notes": "",
        "Charge Code": "",
        "Priority": "",
        "Status": "",
        "Billable": ""
    });

    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(rows);
    const shortName = getMemberShortName(member);
    XLSX.utils.book_append_sheet(wb, ws, `${shortName} Week`);
    XLSX.writeFile(wb, `Timesheet_${member.name.replace(/\s+/g, '_')}_${weekDates[0]}_to_${weekDates[4]}.xlsx`);
    showToast(`Exported timesheet for ${member.name} to Excel`);
}

async function exportSingleMemberWeeklyPDF(memberId, weekDates, allTasks) {
    if (!window.jspdf || !window.jspdf.jsPDF) return alert('Loading PDF...');
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const member = state.members.find(m => m.id === memberId) || { name: memberId, role: 'Analyst', location: 'Global' };
    const tasks = (allTasks || await dataStore.getAllTasks()).filter(t => t.memberId === memberId && weekDates.includes(t.date));

    doc.setFontSize(16);
    doc.setTextColor(0, 20, 137);
    doc.text(`Weekly Timesheet — ${member.name}`, 14, 18);

    doc.setFontSize(10);
    doc.setTextColor(113, 110, 133);
    doc.text(`${member.role} • ${member.location} | Week: ${weekDates[0]} to ${weekDates[4]}`, 14, 25);

    const body = tasks.map(t => [
        t.date,
        t.description,
        t.category || 'General',
        t.thingsRequired || '-',
        `${(parseFloat(t.hours) || 0).toFixed(1)}h`,
        (t.priority || 'normal').toUpperCase(),
        (t.status || 'completed').toUpperCase()
    ]);

    const totH = tasks.reduce((s, t) => s + (parseFloat(t.hours) || 0), 0);
    body.push(['TOTAL', `${tasks.length} tasks recorded`, '', '', `${totH.toFixed(1)}h`, '', '']);

    doc.autoTable({
        startY: 32,
        head: [['Date', 'Task Description', 'Charge Code', 'Work Order / Ref', 'Hours', 'Priority', 'Status']],
        body: body,
        theme: 'striped',
        headStyles: { fillColor: [0, 20, 137] }
    });

    doc.save(`Timesheet_${member.name.replace(/\s+/g, '_')}_${weekDates[0]}_to_${weekDates[4]}.pdf`);
    showToast(`Downloaded timesheet PDF for ${member.name}`);
}

async function exportTimesheetXLSX() {
    const all = await dataStore.getAllTasks();
    const dates = getWeekDates(state.currentTimesheetMonday);

    if (state.tsMemberFilter && state.tsMemberFilter !== 'all') {
        return exportSingleMemberWeeklyXLSX(state.tsMemberFilter, dates, all);
    }

    if (typeof XLSX === 'undefined') return alert('Loading Excel...');
    const weekTasks = all.filter(t => dates.includes(t.date));

    const rows = state.members.map(m => {
        const mTasks = weekTasks.filter(t => t.memberId === m.id);
        const daily = [0, 0, 0, 0, 0];
        mTasks.forEach(t => {
            const idx = dates.indexOf(t.date);
            if (idx >= 0 && idx < 5) daily[idx] += parseFloat(t.hours) || 0;
        });
        return {
            "Member Name": m.name,
            "Role": m.role,
            "Mon": daily[0],
            "Tue": daily[1],
            "Wed": daily[2],
            "Thu": daily[3],
            "Fri": daily[4],
            "Total Weekly Hours": daily.reduce((a, b) => a + b, 0)
        };
    });

    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(rows);
    XLSX.utils.book_append_sheet(wb, ws, "Weekly Timesheet");
    XLSX.writeFile(wb, `Chevron_Timesheet_Team_${dates[0]}_to_${dates[4]}.xlsx`);
    showToast('Exported team weekly timesheet to Excel');
}

async function exportTimesheetPDF() {
    const all = await dataStore.getAllTasks();
    const dates = getWeekDates(state.currentTimesheetMonday);

    if (state.tsMemberFilter && state.tsMemberFilter !== 'all') {
        return exportSingleMemberWeeklyPDF(state.tsMemberFilter, dates, all);
    }

    if (!window.jspdf || !window.jspdf.jsPDF) return alert('Loading PDF...');
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const weekTasks = all.filter(t => dates.includes(t.date));

    doc.setFontSize(16);
    doc.setTextColor(0, 20, 137);
    doc.text("Chevron Team Weekly Timesheet | Pinnacle", 14, 18);

    doc.setFontSize(10);
    doc.setTextColor(113, 110, 133);
    doc.text(`Team Summary | Week: ${dates[0]} to ${dates[4]}`, 14, 25);

    const body = state.members.map(m => {
        const mTasks = weekTasks.filter(t => t.memberId === m.id);
        const daily = [0, 0, 0, 0, 0];
        mTasks.forEach(t => {
            const idx = dates.indexOf(t.date);
            if (idx >= 0 && idx < 5) daily[idx] += parseFloat(t.hours) || 0;
        });
        return [m.name, m.role, daily[0] || '-', daily[1] || '-', daily[2] || '-', daily[3] || '-', daily[4] || '-', `${daily.reduce((a,b)=>a+b,0).toFixed(1)}h`];
    });

    doc.autoTable({
        startY: 32,
        head: [['Member Name', 'Role', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Total']],
        body: body,
        theme: 'striped',
        headStyles: { fillColor: [0, 20, 137] }
    });

    doc.save(`Chevron_Team_Timesheet_${dates[0]}_to_${dates[4]}.pdf`);
    showToast('Downloaded team timesheet PDF');
}

async function initApp() {
    const hasInitialized = localStorage.getItem('chevron_has_initialized');
    const loaded = loadLocalCache();
    if (!hasInitialized && (!loaded || state.allTasksCache.length === 0)) {
        state.allTasksCache = getInitialDemoTasks();
        localStorage.setItem('chevron_has_initialized', 'true');
        saveLocalCache();
    }
    populateMemberDropdowns();
    setupListeners();
    updateTsLabel();
    await refreshAll();

    // Connect to Firebase in background for real-time cloud sync
    try {
        await dataStore.init();
    } catch (e) {
        console.warn('[DBMS] Firebase background init notice:', e);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
