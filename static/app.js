"use strict";

(function initializeDashboardApp() {
    if (window.__officeDashboardAppInitialized) {
        return;
    }
    window.__officeDashboardAppInitialized = true;

    const TICK_INTERVAL_MS = 1000;
    const SYNC_INTERVAL_MS = 30000;
    const STATUS_ENDPOINT = "/api/status";
    const TODAY_ENDPOINT = "/api/today";

    const dom = {
        connectionStatus: null,
        connectionLabel: null,
        currentSsid: null,
        startTime: null,
        syncStatus: null,
        timerModeLabel: null,
        timerDisplay: null,
        progressPercent: null,
        progressTrack: null,
        progressFill: null,
        completionBanner: null,
        completedTotal: null,
        todaySessionsBody: null,
        todayTotalDisplay: null,
        notificationBadge: null,
        tabLive: null,
        tabToday: null,
        tabWeekly: null,
        weeklyTableBody: null,
        weeklyTotalHours: null,
        weeklyAvgHours: null,
        weeklyTargetsMet: null,
        currentWeekLabel: null,
        prevWeekBtn: null,
        nextWeekBtn: null,
        weeklyChartCanvas: null,
    };

    const state = {
        status: null,
        today: null,
        weekly: null,
        syncAtMs: null,
        sessionStartMs: null,
        baseElapsedSeconds: 0,
        baseRemainingSeconds: 0,
        targetSeconds: null,
        lastCompleted4h: null,
        activeTab: "live",
        selectedWeek: null, // YYYY-Www
        charts: {
            weekly: null
        }
    };

    function cacheElements() {
        dom.connectionStatus = document.getElementById("connection-status");
        dom.connectionLabel = document.getElementById("connection-label");
        dom.currentSsid = document.getElementById("current-ssid");
        dom.startTime = document.getElementById("start-time");
        dom.syncStatus = document.getElementById("sync-status");
        dom.timerModeLabel = document.getElementById("timer-mode-label");
        dom.timerDisplay = document.getElementById("timer-display");
        dom.progressPercent = document.getElementById("progress-percent");
        dom.progressFill = document.getElementById("progress-fill");
        dom.progressTrack = document.querySelector(".progress-track");
        dom.completionBanner = document.getElementById("completion-banner");
        dom.completedTotal = document.getElementById("completed-total");
        dom.todaySessionsBody = document.getElementById("today-sessions-body");
        dom.todayTotalDisplay = document.getElementById("today-total-display");
        dom.notificationBadge = document.getElementById("notification-status-badge");
        
        dom.tabLive = document.getElementById("tab-live");
        dom.tabToday = document.getElementById("tab-today");
        dom.tabWeekly = document.getElementById("tab-weekly");
        
        dom.weeklyTableBody = document.getElementById("weekly-table-body");
        dom.weeklyTotalHours = document.getElementById("weekly-total-hours");
        dom.weeklyAvgHours = document.getElementById("weekly-avg-hours");
        dom.weeklyTargetsMet = document.getElementById("weekly-targets-met");
        dom.currentWeekLabel = document.getElementById("current-week-label");
        dom.prevWeekBtn = document.getElementById("prev-week");
        dom.nextWeekBtn = document.getElementById("next-week");
        dom.weeklyChartCanvas = document.getElementById("weekly-chart");
    }

    function hasRequiredDom() {
        return Boolean(
            dom.connectionStatus &&
            dom.connectionLabel &&
            dom.startTime &&
            dom.timerModeLabel &&
            dom.timerDisplay &&
            dom.progressPercent &&
            dom.progressFill &&
            dom.completionBanner &&
            dom.completedTotal &&
            dom.todaySessionsBody &&
            dom.todayTotalDisplay &&
            dom.tabLive &&
            dom.tabToday &&
            dom.tabWeekly
        );
    }

    // --- Helpers ---

    function getISOWeek(date) {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        const weekNo = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
        return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, "0")}`;
    }

    function addWeeks(weekStr, n) {
        const match = weekStr.match(/^(\d{4})-W(\d{2})$/);
        if (!match) return weekStr;
        const year = parseInt(match[1]);
        const week = parseInt(match[2]);
        
        // Simple but effective: move to a Thursday in that week, then add 7*n days
        const jan4 = new Date(year, 0, 4);
        const dayNum = jan4.getDay() || 7;
        const thursOfFirstWeek = new Date(jan4.getTime() + (4 - dayNum) * 86400000);
        const targetThurs = new Date(thursOfFirstWeek.getTime() + (week - 1) * 7 * 86400000 + n * 7 * 86400000);
        
        return getISOWeek(targetThurs);
    }

    // --- Tab Management ---

    function switchTab(tabId) {
        state.activeTab = tabId;
        
        // Update tabs UI
        document.querySelectorAll(".tab").forEach(tab => {
            tab.classList.toggle("active", tab.dataset.tab === tabId);
        });
        
        // Update content visibility
        dom.tabLive.classList.toggle("hidden", tabId !== "live");
        dom.tabToday.classList.toggle("hidden", tabId !== "today");
        dom.tabWeekly.classList.toggle("hidden", tabId !== "weekly");
        
        if (tabId === "weekly") {
            if (!state.selectedWeek) {
                state.selectedWeek = getISOWeek(new Date());
            }
            void syncWeekly();
        }
    }

    // --- Analytics Rendering ---

    function renderWeeklyTable() {
        if (!state.weekly || !dom.weeklyTableBody) return;
        
        dom.weeklyTableBody.innerHTML = "";
        state.weekly.days.forEach(day => {
            const row = document.createElement("tr");
            
            const dateCell = document.createElement("td");
            dateCell.textContent = day.date;
            
            const dayCell = document.createElement("td");
            dayCell.textContent = day.day;
            
            const hoursCell = document.createElement("td");
            hoursCell.textContent = formatMinutes(day.total_minutes);
            
            const sessionsCell = document.createElement("td");
            sessionsCell.textContent = day.session_count;
            
            const statusCell = document.createElement("td");
            statusCell.textContent = day.target_met ? "✅ Met" : "❌ No";
            statusCell.className = day.target_met ? "connected" : "muted";
            
            row.appendChild(dateCell);
            row.appendChild(dayCell);
            row.appendChild(hoursCell);
            row.appendChild(sessionsCell);
            row.appendChild(statusCell);
            dom.weeklyTableBody.appendChild(row);
        });
        
        dom.weeklyTotalHours.textContent = formatMinutes(state.weekly.total_minutes);
        dom.weeklyAvgHours.textContent = formatMinutes(Math.round(state.weekly.avg_minutes_per_day));
        dom.weeklyTargetsMet.textContent = `${state.weekly.days_target_met} / 7`;
        dom.currentWeekLabel.textContent = state.weekly.week;
    }

    function renderWeeklyChart() {
        if (!state.weekly || !dom.weeklyChartCanvas) return;
        
        const ctx = dom.weeklyChartCanvas.getContext("2d");
        const labels = state.weekly.days.map(d => d.day);
        const data = state.weekly.days.map(d => d.total_minutes / 60);
        const colors = state.weekly.days.map(d => d.target_met ? "#22c55e" : "#ef4444");

        if (state.charts.weekly) {
            state.charts.weekly.destroy();
        }

        // Get target hours from backend status or default to 4
        const targetHours = state.status ? (state.targetSeconds / 3600) : 4.16; // 4h 10m fallback

        state.charts.weekly = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Hours Worked",
                    data: data,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Hours"
                        },
                        suggestedMax: 6
                    }
                },
                plugins: {
                    annotation: { // Note: standard chart.js doesn't include annotation plugin by default, 
                                 // we'll use a simple horizontal line if we wanted, 
                                 // but for now let's just use standard bar chart.
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    async function syncWeekly() {
        try {
            const url = `/api/weekly${state.selectedWeek ? `?week=${state.selectedWeek}` : ""}`;
            const data = await fetchJson(url);
            state.weekly = data;
            state.selectedWeek = data.week;
            renderWeeklyTable();
            renderWeeklyChart();
            clearSyncError();
        } catch (error) {
            console.warn("Weekly sync failed:", error);
            showSyncError("Failed to load weekly analytics.");
        }
    }

    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function toInt(value, defaultValue) {
        const parsed = Number(value);
        if (!Number.isFinite(parsed)) {
            return defaultValue;
        }
        return Math.trunc(parsed);
    }

    function formatHHMMSS(totalSeconds) {
        const safeSeconds = Math.max(0, toInt(totalSeconds, 0));
        const hours = Math.floor(safeSeconds / 3600);
        const minutes = Math.floor((safeSeconds % 3600) / 60);
        const seconds = safeSeconds % 60;
        return [
            String(hours).padStart(2, "0"),
            String(minutes).padStart(2, "0"),
            String(seconds).padStart(2, "0"),
        ].join(":");
    }

    function formatMinutes(totalMinutes) {
        if (totalMinutes === null || totalMinutes === undefined) {
            return "-";
        }
        const safeMinutes = Math.max(0, toInt(totalMinutes, 0));
        const hours = Math.floor(safeMinutes / 60);
        const minutes = safeMinutes % 60;
        return `${hours}h ${String(minutes).padStart(2, "0")}m`;
    }

    function formatPercent(value) {
        const clamped = clamp(Number(value) || 0, 0, 100);
        if (Number.isInteger(clamped)) {
            return `${clamped}%`;
        }
        return `${clamped.toFixed(1)}%`;
    }

    function parseSessionStartMs(dateToken, startTime) {
        if (typeof dateToken !== "string" || typeof startTime !== "string") {
            return null;
        }
        const dateMatch = dateToken.match(/^(\d{2})-(\d{2})-(\d{4})$/);
        const timeMatch = startTime.match(/^(\d{2}):(\d{2}):(\d{2})$/);
        if (!dateMatch || !timeMatch) {
            return null;
        }
        const day = Number(dateMatch[1]);
        const month = Number(dateMatch[2]) - 1;
        const year = Number(dateMatch[3]);
        const hour = Number(timeMatch[1]);
        const minute = Number(timeMatch[2]);
        const second = Number(timeMatch[3]);
        const timestamp = new Date(year, month, day, hour, minute, second).getTime();
        if (!Number.isFinite(timestamp)) {
            return null;
        }
        return timestamp;
    }

    function getLocalDateToken() {
        const now = new Date();
        const day = String(now.getDate()).padStart(2, "0");
        const month = String(now.getMonth() + 1).padStart(2, "0");
        const year = String(now.getFullYear());
        return `${day}-${month}-${year}`;
    }

    function applyStatus(statusPayload) {
        const newCompleted4h = Boolean(statusPayload.completed_4h);

        // Notify if it just flipped to true
        if (state.lastCompleted4h === false && newCompleted4h === true) {
            notifyCompletion();
        }

        state.lastCompleted4h = newCompleted4h;
        state.status = statusPayload;
        state.syncAtMs = Date.now();
        state.baseElapsedSeconds = toInt(statusPayload.elapsed_seconds, 0);
        state.baseRemainingSeconds = toInt(statusPayload.remaining_seconds, 0);

        const derivedTarget = state.baseElapsedSeconds + state.baseRemainingSeconds;
        state.targetSeconds = derivedTarget > 0 ? derivedTarget : null;

        const sessionDate =
            state.today && typeof state.today.date === "string"
                ? state.today.date
                : getLocalDateToken();
        state.sessionStartMs = parseSessionStartMs(sessionDate, statusPayload.start_time);
    }

    function applyToday(todayPayload) {
        state.today = todayPayload;
    }

    function updateNotificationBadge() {
        if (!dom.notificationBadge) {
            return;
        }

        if (!("Notification" in window)) {
            dom.notificationBadge.textContent = "Unsupported";
            dom.notificationBadge.className = "badge badge-danger";
            dom.notificationBadge.classList.remove("hidden");
            return;
        }

        const permission = Notification.permission;
        dom.notificationBadge.classList.remove("hidden");

        if (permission === "granted") {
            dom.notificationBadge.textContent = "Alerts On";
            dom.notificationBadge.className = "badge badge-success";
            dom.notificationBadge.title = "Notifications enabled";
        } else if (permission === "denied") {
            dom.notificationBadge.textContent = "Alerts Blocked";
            dom.notificationBadge.className = "badge badge-danger";
            dom.notificationBadge.title = "Blocked in browser settings";
        } else {
            dom.notificationBadge.textContent = "Alerts Off";
            dom.notificationBadge.className = "badge badge-warning";
            dom.notificationBadge.style.cursor = "pointer";
            dom.notificationBadge.title = "Click to enable alerts";
            if (!dom.notificationBadge._hasListener) {
                dom.notificationBadge.addEventListener("click", () => {
                    requestNotificationPermission();
                });
                dom.notificationBadge._hasListener = true;
            }
        }
    }

    function requestNotificationPermission() {
        if (!("Notification" in window)) {
            console.warn("This browser does not support desktop notifications.");
            updateNotificationBadge();
            return;
        }
        if (Notification.permission === "default") {
            Notification.requestPermission().then(() => {
                updateNotificationBadge();
            });
        } else {
            updateNotificationBadge();
        }
    }

    function notifyCompletion() {
        if (!("Notification" in window) || Notification.permission !== "granted") {
            return;
        }
        try {
            new Notification("Office Wi-Fi Tracker", {
                body: "4-hour target reached (including buffer). You're all set!",
            });
        } catch (err) {
            console.error("Failed to show notification:", err);
        }
    }

    function getLiveElapsedSeconds() {
        if (!state.status || !state.status.session_active) {
            return 0;
        }
        if (state.sessionStartMs !== null) {
            return Math.max(0, Math.floor((Date.now() - state.sessionStartMs) / 1000));
        }
        if (state.syncAtMs === null) {
            return Math.max(0, state.baseElapsedSeconds);
        }
        const driftSeconds = Math.floor((Date.now() - state.syncAtMs) / 1000);
        return Math.max(0, state.baseElapsedSeconds + driftSeconds);
    }

    function getLiveRemainingSeconds(elapsedSeconds) {
        if (!state.status) {
            return 0;
        }
        if (!state.status.session_active) {
            return Math.max(0, toInt(state.status.remaining_seconds, 0));
        }
        if (state.targetSeconds !== null) {
            return state.targetSeconds - elapsedSeconds;
        }
        if (state.syncAtMs === null) {
            return state.baseRemainingSeconds;
        }
        const driftSeconds = Math.floor((Date.now() - state.syncAtMs) / 1000);
        return state.baseRemainingSeconds - driftSeconds;
    }

    function getLiveProgressPercent(elapsedSeconds, completed) {
        if (completed) {
            return 100;
        }
        if (state.targetSeconds && state.targetSeconds > 0) {
            return clamp((elapsedSeconds / state.targetSeconds) * 100, 0, 100);
        }
        if (state.status && Number.isFinite(state.status.progress_percent)) {
            return clamp(state.status.progress_percent, 0, 100);
        }
        return 0;
    }

    function renderConnection() {
        if (!state.status) {
            return;
        }
        const isConnected = Boolean(state.status.connected);
        const ssid = state.status.ssid || "-";

        dom.connectionStatus.classList.toggle("connected", isConnected);
        dom.connectionStatus.classList.toggle("disconnected", !isConnected);

        dom.connectionLabel.textContent = isConnected ? "Connected to" : "Disconnected";
        dom.currentSsid.textContent = ssid;
    }

    function renderStartTime() {
        if (!state.status) {
            return;
        }
        if (state.status.session_active && typeof state.status.start_time === "string") {
            dom.startTime.textContent = state.status.start_time;
            return;
        }
        dom.startTime.textContent = "--:--:--";
    }

    function updateProgressClasses(progressValue, completed) {
        const warning = !completed && progressValue >= 75;
        dom.timerDisplay.classList.toggle("warning", warning);
        dom.timerDisplay.classList.toggle("completed", completed);
        dom.progressFill.classList.toggle("warning", warning);
        dom.progressFill.classList.toggle("complete", completed);
    }

    function renderTimer() {
        if (!state.status) {
            return;
        }

        if (!state.status.session_active) {
            const targetDisplay = state.status.target_display || "--";
            dom.timerModeLabel.textContent = `Waiting for office session (target: ${targetDisplay})`;
            dom.timerDisplay.textContent = "00:00:00";
            dom.progressPercent.textContent = "0%";
            dom.progressFill.style.width = "0%";
            if (dom.progressTrack) {
                dom.progressTrack.setAttribute("aria-valuenow", "0");
            }
            dom.completionBanner.classList.add("hidden");
            updateProgressClasses(0, false);
            return;
        }

        const elapsedSeconds = getLiveElapsedSeconds();
        const remainingSeconds = getLiveRemainingSeconds(elapsedSeconds);
        const completed = Boolean(state.status.completed_4h) || remainingSeconds <= 0;
        const progressValue = getLiveProgressPercent(elapsedSeconds, completed);
        const targetDisplay = state.status.target_display || "--";

        if (completed) {
            dom.timerModeLabel.textContent = `Completed (target: ${targetDisplay})`;
            dom.timerDisplay.textContent = formatHHMMSS(elapsedSeconds);
            dom.completedTotal.textContent = formatHHMMSS(elapsedSeconds);
            dom.completionBanner.classList.remove("hidden");
        } else {
            dom.timerModeLabel.textContent = `Remaining (target: ${targetDisplay})`;
            dom.timerDisplay.textContent = formatHHMMSS(Math.max(0, remainingSeconds));
            dom.completionBanner.classList.add("hidden");
        }

        dom.progressPercent.textContent = formatPercent(progressValue);
        dom.progressFill.style.width = `${clamp(progressValue, 0, 100)}%`;
        if (dom.progressTrack) {
            dom.progressTrack.setAttribute("aria-valuenow", String(Math.round(progressValue)));
        }
        updateProgressClasses(progressValue, completed);
    }

    function getSessionStatusText(session) {
        if (!session) {
            return "Unknown";
        }
        const active = session.end_time === null;
        if (active) {
            return session.completed_4h ? "Completed (Active)" : "Active";
        }
        return session.completed_4h ? "Completed" : "Ended";
    }

    function renderTodaySessions() {
        if (!state.today || !Array.isArray(state.today.sessions)) {
            return;
        }

        dom.todaySessionsBody.textContent = "";
        if (state.today.sessions.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");
            cell.colSpan = 4;
            cell.textContent = "No sessions for today.";
            row.appendChild(cell);
            dom.todaySessionsBody.appendChild(row);
        } else {
            for (const session of state.today.sessions) {
                const row = document.createElement("tr");
                const startCell = document.createElement("td");
                const endCell = document.createElement("td");
                const durationCell = document.createElement("td");
                const statusCell = document.createElement("td");

                startCell.textContent = session.start_time || "-";
                endCell.textContent = session.end_time || "-";
                durationCell.textContent = formatMinutes(session.duration_minutes);
                statusCell.textContent = getSessionStatusText(session);

                row.appendChild(startCell);
                row.appendChild(endCell);
                row.appendChild(durationCell);
                row.appendChild(statusCell);
                dom.todaySessionsBody.appendChild(row);
            }
        }

        dom.todayTotalDisplay.textContent = state.today.total_display || "0h 00m";
    }

    function showSyncError(message) {
        if (!dom.syncStatus) {
            return;
        }
        dom.syncStatus.textContent = message;
        dom.syncStatus.classList.remove("hidden");
        dom.syncStatus.classList.add("error");
    }

    function clearSyncError() {
        if (!dom.syncStatus) {
            return;
        }
        dom.syncStatus.textContent = "";
        dom.syncStatus.classList.add("hidden");
        dom.syncStatus.classList.remove("error");
    }

    async function fetchJson(url) {
        const response = await fetch(url, {cache: "no-store"});
        if (!response.ok) {
            throw new Error(`Request failed: ${url} (${response.status})`);
        }
        return response.json();
    }

    function renderAll() {
        renderConnection();
        renderStartTime();
        renderTimer();
        renderTodaySessions();
    }

    async function syncFromBackend() {
        try {
            const [statusPayload, todayPayload] = await Promise.all([
                fetchJson(STATUS_ENDPOINT),
                fetchJson(TODAY_ENDPOINT),
            ]);
            applyToday(todayPayload);
            applyStatus(statusPayload);
            clearSyncError();
            renderAll();
        } catch (error) {
            console.warn("Dashboard sync failed:", error);
            showSyncError("Live sync delayed. Showing last known data.");
            renderAll();
        }
    }

    function start() {
        cacheElements();
        if (!hasRequiredDom()) {
            return;
        }

        // Tab wiring
        document.querySelectorAll(".tab").forEach(tab => {
            tab.addEventListener("click", () => {
                const tabId = tab.dataset.tab;
                if (tabId && !tab.textContent.includes("(Soon)")) {
                    switchTab(tabId);
                }
            });
        });

        // Week selector wiring
        if (dom.prevWeekBtn) {
            dom.prevWeekBtn.addEventListener("click", () => {
                state.selectedWeek = addWeeks(state.selectedWeek, -1);
                void syncWeekly();
            });
        }
        if (dom.nextWeekBtn) {
            dom.nextWeekBtn.addEventListener("click", () => {
                state.selectedWeek = addWeeks(state.selectedWeek, 1);
                void syncWeekly();
            });
        }

        requestNotificationPermission();
        updateNotificationBadge();
        void syncFromBackend();
        setInterval(renderTimer, TICK_INTERVAL_MS);
        setInterval(() => {
            void syncFromBackend();
            if (state.activeTab === "weekly") {
                void syncWeekly();
            }
        }, SYNC_INTERVAL_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
