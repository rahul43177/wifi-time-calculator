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
        elapsedDisplay: null,
        elapsedTime: null,
        targetDisplay: null,
        elapsedPercent: null,
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
        tabMonthly: null,
        monthlyTableBody: null,
        monthlyTotalHours: null,
        monthlyTotalDays: null,
        monthlyAvgHours: null,
        currentMonthLabel: null,
        prevMonthBtn: null,
        nextMonthBtn: null,
        monthlyChartCanvas: null,
        // Task 7.2: Status cards
        cardConnection: null,
        cardConnectionIcon: null,
        cardConnectionValue: null,
        cardConnectionDetail: null,
        cardSessionValue: null,
        cardSessionDetail: null,
        cardTodayValue: null,
        cardTodayDetail: null,
        cardTarget: null,
        cardTargetValue: null,
        cardTargetDetail: null,
    };

    const state = {
        status: null,
        today: null,
        weekly: null,
        monthly: null,
        syncAtMs: null,
        sessionStartMs: null,
        baseElapsedSeconds: 0,
        baseRemainingSeconds: 0,
        targetSeconds: null,
        lastCompleted4h: null,
        activeTab: "live",
        selectedWeek: null, // YYYY-Www
        selectedMonth: null, // YYYY-MM
        charts: {
            weekly: null,
            monthly: null
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
        dom.elapsedDisplay = document.getElementById("elapsed-display");
        dom.elapsedTime = document.getElementById("elapsed-time");
        dom.targetDisplay = document.getElementById("target-display");
        dom.elapsedPercent = document.getElementById("elapsed-percent");
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

        dom.tabMonthly = document.getElementById("tab-monthly");
        dom.monthlyTableBody = document.getElementById("monthly-table-body");
        dom.monthlyTotalHours = document.getElementById("monthly-total-hours");
        dom.monthlyTotalDays = document.getElementById("monthly-total-days");
        dom.monthlyAvgHours = document.getElementById("monthly-avg-hours");
        dom.currentMonthLabel = document.getElementById("current-month-label");
        dom.prevMonthBtn = document.getElementById("prev-month");
        dom.nextMonthBtn = document.getElementById("next-month");
        dom.monthlyChartCanvas = document.getElementById("monthly-chart");

        // Task 7.2: Status cards
        dom.cardConnection = document.getElementById("card-connection");
        dom.cardConnectionIcon = document.getElementById("connection-icon");
        dom.cardConnectionValue = document.getElementById("card-connection-value");
        dom.cardConnectionDetail = document.getElementById("card-connection-detail");
        dom.cardSessionValue = document.getElementById("card-session-value");
        dom.cardSessionDetail = document.getElementById("card-session-detail");
        dom.cardTodayValue = document.getElementById("card-today-value");
        dom.cardTodayDetail = document.getElementById("card-today-detail");
        dom.cardTarget = document.getElementById("card-target");
        dom.cardTargetValue = document.getElementById("card-target-value");
        dom.cardTargetDetail = document.getElementById("card-target-detail");
    }

    function hasRequiredDom() {
        return Boolean(
            dom.connectionStatus &&
            dom.connectionLabel &&
            dom.startTime &&
            dom.timerModeLabel &&
            dom.timerDisplay &&
            dom.elapsedDisplay &&
            dom.elapsedTime &&
            dom.targetDisplay &&
            dom.elapsedPercent &&
            dom.progressFill &&
            dom.completionBanner &&
            dom.completedTotal &&
            dom.todaySessionsBody &&
            dom.todayTotalDisplay &&
            dom.tabLive &&
            dom.tabToday &&
            dom.tabWeekly &&
            dom.tabMonthly
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

    function addMonths(monthStr, n) {
        const [year, month] = monthStr.split("-").map(Number);
        const date = new Date(year, month - 1 + n, 1);
        const newYear = date.getFullYear();
        const newMonth = String(date.getMonth() + 1).padStart(2, "0");
        return `${newYear}-${newMonth}`;
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
        dom.tabMonthly.classList.toggle("hidden", tabId !== "monthly");
        
        if (tabId === "weekly") {
            if (!state.selectedWeek) {
                state.selectedWeek = getISOWeek(new Date());
            }
            void syncWeekly();
        } else if (tabId === "monthly") {
            if (!state.selectedMonth) {
                const now = new Date();
                state.selectedMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
            }
            void syncMonthly();
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
                datasets: [
                    {
                        label: "Hours Worked",
                        data: data,
                        backgroundColor: colors,
                        borderRadius: 4,
                        order: 2
                    },
                    {
                        label: `Target (${formatMinutes(Math.round(targetHours * 60))})`,
                        data: Array(7).fill(targetHours),
                        type: "line",
                        borderColor: "#f59e0b",
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false,
                        order: 1
                    }
                ]
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
                        suggestedMax: Math.max(6, targetHours + 1)
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: "top",
                        align: "end",
                        labels: {
                            boxWidth: 12,
                            usePointStyle: true,
                            pointStyle: "circle"
                        }
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

    function renderMonthlyTable() {
        if (!state.monthly || !dom.monthlyTableBody) return;
        
        dom.monthlyTableBody.innerHTML = "";
        state.monthly.weeks.forEach(week => {
            const row = document.createElement("tr");
            
            const weekCell = document.createElement("td");
            weekCell.textContent = week.week;
            
            const startCell = document.createElement("td");
            startCell.textContent = week.start_date;
            
            const endCell = document.createElement("td");
            endCell.textContent = week.end_date;
            
            const hoursCell = document.createElement("td");
            hoursCell.textContent = formatMinutes(week.total_minutes);
            
            const daysCell = document.createElement("td");
            daysCell.textContent = week.days_present;
            
            const avgCell = document.createElement("td");
            avgCell.textContent = formatMinutes(Math.round(week.avg_daily_minutes));
            
            row.appendChild(weekCell);
            row.appendChild(startCell);
            row.appendChild(endCell);
            row.appendChild(hoursCell);
            row.appendChild(daysCell);
            row.appendChild(avgCell);
            dom.monthlyTableBody.appendChild(row);
        });
        
        dom.monthlyTotalHours.textContent = formatMinutes(state.monthly.total_minutes);
        dom.monthlyTotalDays.textContent = state.monthly.total_days_present;
        dom.monthlyAvgHours.textContent = formatMinutes(Math.round(state.monthly.avg_daily_minutes));
        dom.currentMonthLabel.textContent = state.monthly.month;
    }

    function renderMonthlyChart() {
        if (!state.monthly || !dom.monthlyChartCanvas) return;
        
        const ctx = dom.monthlyChartCanvas.getContext("2d");
        const labels = state.monthly.weeks.map(w => w.week);
        const data = state.monthly.weeks.map(w => w.total_minutes / 60);

        if (state.charts.monthly) {
            state.charts.monthly.destroy();
        }

        state.charts.monthly = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Hours Worked",
                    data: data,
                    borderColor: "#4f46e5",
                    backgroundColor: "rgba(79, 70, 229, 0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5,
                    pointBackgroundColor: "#4f46e5"
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
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    async function syncMonthly() {
        try {
            const url = `/api/monthly${state.selectedMonth ? `?month=${state.selectedMonth}` : ""}`;
            const data = await fetchJson(url);
            state.monthly = data;
            state.selectedMonth = data.month;
            renderMonthlyTable();
            renderMonthlyChart();
            clearSyncError();
        } catch (error) {
            console.warn("Monthly sync failed:", error);
            showSyncError("Failed to load monthly analytics.");
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

    function formatSecondsToHM(totalSeconds) {
        const safeSeconds = Math.max(0, toInt(totalSeconds, 0));
        const totalMinutes = Math.floor(safeSeconds / 60);
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;
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

        // Legacy status line (kept for backward compatibility)
        if (dom.connectionStatus) {
            dom.connectionStatus.classList.toggle("connected", isConnected);
            dom.connectionStatus.classList.toggle("disconnected", !isConnected);
        }
        if (dom.connectionLabel) {
            dom.connectionLabel.textContent = isConnected ? "Connected to" : "Disconnected";
        }
        if (dom.currentSsid) {
            dom.currentSsid.textContent = ssid;
        }
    }

    // Task 7.2: Render status cards
    function renderStatusCards() {
        if (!state.status) {
            return;
        }

        const isConnected = Boolean(state.status.connected);
        const ssid = state.status.ssid || "-";
        const sessionActive = Boolean(state.status.session_active);
        const elapsedSeconds = getLiveElapsedSeconds();
        const remainingSeconds = getLiveRemainingSeconds(elapsedSeconds);
        const completed = Boolean(state.status.completed_4h) || remainingSeconds <= 0;
        const progressValue = getLiveProgressPercent(elapsedSeconds, completed);
        const targetDisplay = state.status.target_display || "4h 10m";

        // Card 1: Connection Status
        if (dom.cardConnection && dom.cardConnectionIcon && dom.cardConnectionValue && dom.cardConnectionDetail) {
            dom.cardConnection.classList.toggle("connected", isConnected);
            dom.cardConnection.classList.toggle("disconnected", !isConnected);
            dom.cardConnectionIcon.textContent = isConnected ? "🌐" : "⚠️";
            dom.cardConnectionValue.textContent = isConnected ? "Connected" : "Disconnected";
            dom.cardConnectionDetail.textContent = ssid;
        }

        // Card 2: Session Details
        if (dom.cardSessionValue && dom.cardSessionDetail) {
            if (sessionActive) {
                dom.cardSessionValue.textContent = state.status.start_time || "--:--:--";
                dom.cardSessionDetail.textContent = `${formatSecondsToHM(elapsedSeconds)} elapsed`;
            } else {
                dom.cardSessionValue.textContent = "--:--:--";
                dom.cardSessionDetail.textContent = "No active session";
            }
        }

        // Card 3: Today's Total
        if (dom.cardTodayValue && dom.cardTodayDetail) {
            const todayTotal = state.today ? state.today.total_display : "0h 00m";
            const sessionCount = state.today && Array.isArray(state.today.sessions) ? state.today.sessions.length : 0;
            dom.cardTodayValue.textContent = todayTotal;
            dom.cardTodayDetail.textContent = sessionCount === 1 ? "1 session" : `${sessionCount} sessions`;
        }

        // Card 4: Target Progress
        if (dom.cardTarget && dom.cardTargetValue && dom.cardTargetDetail) {
            dom.cardTargetValue.textContent = formatPercent(progressValue);

            // Apply color class based on Task 7.1 thresholds
            dom.cardTarget.classList.remove("progress-low", "progress-medium", "progress-high", "progress-complete");
            if (completed) {
                dom.cardTarget.classList.add("progress-complete");
                dom.cardTargetDetail.textContent = "Target completed!";
            } else if (progressValue > 80) {
                dom.cardTarget.classList.add("progress-high");
                dom.cardTargetDetail.textContent = `${formatHHMMSS(Math.max(0, remainingSeconds))} remaining`;
            } else if (progressValue >= 50) {
                dom.cardTarget.classList.add("progress-medium");
                dom.cardTargetDetail.textContent = `${formatHHMMSS(Math.max(0, remainingSeconds))} remaining`;
            } else {
                dom.cardTarget.classList.add("progress-low");
                dom.cardTargetDetail.textContent = `${targetDisplay} remaining`;
            }
        }
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
        // Align with Task 7.1 threshold model: <50% blue, 50-80% yellow, >80% green
        const warning = !completed && progressValue >= 50 && progressValue <= 80;
        const complete = completed || progressValue > 80;
        dom.progressFill.classList.toggle("warning", warning);
        dom.progressFill.classList.toggle("complete", complete);
    }

    function updateElapsedDisplayColor(progressValue, completed) {
        if (!dom.elapsedDisplay) return;

        // Remove all color classes
        dom.elapsedDisplay.classList.remove("progress-low", "progress-medium", "progress-high", "progress-complete");

        if (completed) {
            dom.elapsedDisplay.classList.add("progress-complete");
        } else if (progressValue > 80) {
            dom.elapsedDisplay.classList.add("progress-high");
        } else if (progressValue >= 50) {
            dom.elapsedDisplay.classList.add("progress-medium");
        } else {
            dom.elapsedDisplay.classList.add("progress-low");
        }
    }

    function renderTimer() {
        if (!state.status) {
            return;
        }

        if (!state.status.session_active) {
            const targetDisplay = state.status.target_display || "4h 10m";
            dom.timerModeLabel.textContent = "Session Progress";

            // Elapsed display
            if (dom.elapsedTime) dom.elapsedTime.textContent = "0h 00m";
            if (dom.targetDisplay) dom.targetDisplay.textContent = targetDisplay;
            if (dom.elapsedPercent) dom.elapsedPercent.textContent = "(0%)";

            // Countdown display
            dom.timerDisplay.textContent = "00:00:00";

            // Progress bar
            dom.progressFill.style.width = "0%";
            if (dom.progressTrack) {
                dom.progressTrack.setAttribute("aria-valuenow", "0");
            }

            dom.completionBanner.classList.add("hidden");
            updateProgressClasses(0, false);
            updateElapsedDisplayColor(0, false);
            return;
        }

        const elapsedSeconds = getLiveElapsedSeconds();
        const remainingSeconds = getLiveRemainingSeconds(elapsedSeconds);
        const completed = Boolean(state.status.completed_4h) || remainingSeconds <= 0;
        const progressValue = getLiveProgressPercent(elapsedSeconds, completed);
        const targetDisplay = state.status.target_display || "4h 10m";

        // Update elapsed display (Task 7.1)
        if (dom.elapsedTime) {
            dom.elapsedTime.textContent = formatSecondsToHM(elapsedSeconds);
        }
        if (dom.targetDisplay) {
            dom.targetDisplay.textContent = targetDisplay;
        }
        if (dom.elapsedPercent) {
            dom.elapsedPercent.textContent = `(${formatPercent(progressValue)})`;
        }

        // Update timer mode label and countdown display
        if (completed) {
            dom.timerModeLabel.textContent = `Completed (target: ${targetDisplay})`;
            dom.timerDisplay.textContent = "00:00:00";
            dom.completedTotal.textContent = formatHHMMSS(elapsedSeconds);
            dom.completionBanner.classList.remove("hidden");
        } else {
            dom.timerModeLabel.textContent = "Session Progress";
            dom.timerDisplay.textContent = formatHHMMSS(Math.max(0, remainingSeconds));
            dom.completionBanner.classList.add("hidden");
        }

        // Update progress bar
        dom.progressFill.style.width = `${clamp(progressValue, 0, 100)}%`;
        if (dom.progressTrack) {
            dom.progressTrack.setAttribute("aria-valuenow", String(Math.round(progressValue)));
        }

        // Apply color coding
        updateProgressClasses(progressValue, completed);
        updateElapsedDisplayColor(progressValue, completed);

        // Task 7.2: Update status cards as part of timer tick
        renderStatusCards();
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
        renderStatusCards(); // Task 7.2
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

        // Month selector wiring
        if (dom.prevMonthBtn) {
            dom.prevMonthBtn.addEventListener("click", () => {
                state.selectedMonth = addMonths(state.selectedMonth, -1);
                void syncMonthly();
            });
        }
        if (dom.nextMonthBtn) {
            dom.nextMonthBtn.addEventListener("click", () => {
                state.selectedMonth = addMonths(state.selectedMonth, 1);
                void syncMonthly();
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
            } else if (state.activeTab === "monthly") {
                void syncMonthly();
            }
        }, SYNC_INTERVAL_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
