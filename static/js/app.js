/**
 * Goal Agent — Frontend Logic (SaaS Refactored)
 * ============================================
 * Handles: split-view UI navigation, accordion expansions,
 * horizontal timeline stepping, and sidebar refinement.
 */

// ────── State ──────
let currentGoal = '';
let currentEvents = [];
let timelineUnit = 'Week';
let activeWeekIdx = 0;

// ────── DOM ──────
const $ = id => document.getElementById(id);
const goalInput = $('goalInput');
const btnGenerate = $('btnGenerate');
const loader = $('loader');
const planSection = $('planSection');
const welcomeView = $('welcomeView');
const chatFooter = $('chatFooter');
const clarifySection = $('clarifySection');
const clarifyQuestions = $('clarifyQuestions');

function show(el) { if(el) el.classList.remove('hidden'); }
function hide(el) { if(el) el.classList.add('hidden'); }
function showLoader(txt) { loader.classList.add('active'); if(txt) console.log(txt); }
function hideLoader() { loader.classList.remove('active'); }

async function api(endpoint, body = {}) {
    const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || 'Request failed');
    }
    return res.json();
}

// ────── Goal Management ──────

function setGoal(text) {
    goalInput.value = text;
    goalInput.focus();
}

async function submitGoal() {
    const goal = goalInput.value.trim();
    if (!goal) { goalInput.focus(); return; }
    currentGoal = goal;

    try {
        btnGenerate.disabled = true;
        showLoader('Analyzing your goal...');
        const data = await api('/start', { goal });

        if (data.status === 'needs_clarification' && data.questions && data.questions.length) {
            currentQuestions = data.questions;
            renderClarification(data.questions);
            show(clarifySection);
            hide(welcomeView);
        } else if (data.plan) {
            currentPlan = data.plan;
            if (data.events) currentEvents = data.events;
            if (data.timeline_unit) timelineUnit = data.timeline_unit;
            
            hide(welcomeView);
            hide(clarifySection);
            renderFullPlan(data.plan);
            show(planSection);
            show(chatFooter);
            $('navCalendarBtn').style.display = 'block';
            
            renderEvents(currentEvents);
        }
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        hideLoader();
        btnGenerate.disabled = false;
    }
}

// ────── Clarification UI ──────

function renderClarification(questions) {
    clarifyQuestions.innerHTML = '';
    questions.forEach((q, idx) => {
        const container = document.createElement('div');
        container.className = 'clarify-item';
        
        const qObj = typeof q === 'string' ? { question: q, options: [] } : q;
        container.innerHTML = `<div class="clarify-q">${escapeHtml(qObj.question)}</div>`;
        
        const pills = document.createElement('div');
        pills.className = 'option-pills';

        if (qObj.options && qObj.options.length) {
            qObj.options.forEach(opt => {
                const pill = document.createElement('span');
                pill.className = 'pill';
                pill.textContent = opt;
                pill.onclick = () => {
                    pills.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
                    pill.classList.add('active');
                };
                pills.appendChild(pill);
            });
        } else {
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'goal-textarea';
            input.placeholder = 'Type your answer...';
            pills.appendChild(input);
        }
        
        container.appendChild(pills);
        clarifyQuestions.appendChild(container);
    });
}

async function submitClarification() {
    const answers = {};
    clarifyQuestions.querySelectorAll('.clarify-item').forEach(item => {
        const q = item.querySelector('.clarify-q').textContent;
        const activePill = item.querySelector('.pill.active');
        const input = item.querySelector('input');
        
        if (activePill) answers[q] = activePill.textContent;
        else if (input && input.value) answers[q] = input.value;
    });

    try {
        showLoader('Generating your plan...');
        const data = await api('/clarify', { goal: currentGoal, answers });
        if (data.plan) {
            currentPlan = data.plan;
            currentEvents = data.events || [];
            timelineUnit = data.timeline_unit || 'Week';
            
            hide(clarifySection);
            renderFullPlan(data.plan);
            show(planSection);
            show(chatFooter);
            $('navCalendarBtn').style.display = 'block';
            renderEvents(currentEvents);
        }
    } catch (err) {
        alert('Error: ' + err.message);
    } finally { hideLoader(); }
}

async function skipClarification() {
    try {
        showLoader('Generating plan...');
        const data = await api('/clarify', { goal: currentGoal, answers: {} });
        if (data.plan) {
            currentPlan = data.plan;
            currentEvents = data.events || [];
            timelineUnit = data.timeline_unit || 'Week';
            
            hide(clarifySection);
            renderFullPlan(data.plan);
            show(planSection);
            show(chatFooter);
            $('navCalendarBtn').style.display = 'block';
            renderEvents(currentEvents);
        }
    } catch (err) { alert('Error: ' + err.message); }
    finally { hideLoader(); }
}

// ────── Plan Rendering (Main Canvas) ──────

function renderFullPlan(plan) {
    // Summary & Stats
    $('goalSummaryText').textContent = plan.goal_summary || '';
    $('goalSummaryText').contentEditable = 'true';
    $('goalSummaryText').onblur = () => currentPlan.goal_summary = $('goalSummaryText').textContent;

    const timeline = plan.timeline || [];
    let totalHours = 0;
    timeline.forEach(w => totalHours += (w.total_hours || 0));
    
    $('statWeeks').textContent = timeline.length;
    $('statHours').textContent = totalHours;
    
    // Intensity badge
    const intensity = totalHours / (timeline.length || 1);
    const intensityLabel = intensity > 20 ? 'High' : intensity > 10 ? 'Medium' : 'Light';
    $('statIntensity').textContent = intensityLabel;
    
    // Update labels in stats row based on unit
    const unitUpper = timelineUnit.toUpperCase();
    const statsRow = $('statWeeks').previousElementSibling;
    if (statsRow) statsRow.textContent = `${unitUpper}S`;

    // Horizontal Stepper
    renderStepper(timeline);

    // Accordions
    renderAccordions(timeline);

    // Resources
    renderResources(plan.resources || []);
}

function renderStepper(weeks) {
    const stepper = $('timelineStepper');
    stepper.innerHTML = '';
    
    weeks.forEach((week, idx) => {
        const card = document.createElement('div');
        card.className = `step-card ${idx === activeWeekIdx ? 'active' : ''}`;
        card.innerHTML = `
            <div class="step-number">${timelineUnit.toUpperCase()} ${idx + 1}</div>
            <div class="step-focus">${escapeHtml(week.title || week.week || week.period || 'Phase')}</div>
            <div class="step-meta">⏱️ ${week.total_hours || 0}h</div>
        `;
        card.onclick = () => {
            activeWeekIdx = idx;
            renderStepper(weeks);
            openWeek(idx);
        };
        stepper.appendChild(card);
    });
}

function renderAccordions(weeks) {
    const container = $('weekBreakdown');
    container.innerHTML = '';
    
    weeks.forEach((week, idx) => {
        const acc = document.createElement('div');
        acc.className = 'week-accordion';
        acc.id = `weekAcc_${idx}`;
        
        const totalTopics = (week.topics || []).length;
        
        acc.innerHTML = `
            <div class="accordion-header" onclick="toggleAccordion(${idx})">
                <div class="accordion-title">
                    <div class="week-num-badge">${idx + 1}</div>
                    <div style="font-weight: 600; font-size: 0.95rem;">${escapeHtml(week.title || week.week || week.period)}</div>
                    <div style="color: var(--text-muted); font-size: 0.8rem;">&middot; ${totalTopics} topics &middot; ${week.total_hours || 0}h/${timelineUnit.toLowerCase()}</div>
                </div>
                <div class="chevron">▾</div>
            </div>
            <div class="accordion-body">
                <div class="sidebar-section-title" style="margin: 12px 0 8px; font-size: 0.65rem;">MILESTONE FOR ${timelineUnit.toUpperCase()} ${idx + 1}</div>
                <div contenteditable="true" style="font-size: 0.85rem; color: var(--success); font-weight: 600; margin-bottom: 20px;">🏆 ${escapeHtml(week.milestone || 'Objective reached')}</div>
                <div class="topics-list">
                    ${renderTopics(week.topics, idx)}
                </div>
            </div>
        `;
        container.appendChild(acc);
    });
}

function renderTopics(topics, weekIdx) {
    if (!topics || !topics.length) return '<p style="font-size: 0.8rem; color: var(--text-muted);">No topics listed.</p>';
    
    return topics.map((t, ti) => `
        <div class="day-row">
            <div class="day-label">GOAL ${ti + 1}</div>
            <div class="task-item">
                <div class="task-content">
                    <h5 contenteditable="true" onblur="updateTopic(${weekIdx}, ${ti}, 'name', this.textContent)">${escapeHtml(t.name)}</h5>
                    <p contenteditable="true" onblur="updateTopic(${weekIdx}, ${ti}, 'description', this.textContent)">${escapeHtml(t.description)}</p>
                </div>
                <div class="task-meta">
                    <span class="duration-tag">${t.hours || 0}h</span>
                    ${t.resource_url && t.resource_url.length > 5
                        ? `<a href="${t.resource_url}" target="_blank" class="resource-link">Resource ↗</a>` 
                        : `<span style="color:var(--text-muted); font-size: 0.7rem;">${escapeHtml(t.resource || 'Research')}</span>`
                    }
                </div>
            </div>
        </div>
    `).join('');
}

function updateTopic(wi, ti, field, val) {
    if (currentPlan && currentPlan.timeline[wi] && currentPlan.timeline[wi].topics[ti]) {
        currentPlan.timeline[wi].topics[ti][field] = val;
    }
}

function toggleAccordion(idx) {
    const acc = document.getElementById(`weekAcc_${idx}`);
    const isOpen = acc.classList.contains('open');
    
    // Close others
    document.querySelectorAll('.week-accordion').forEach(a => a.classList.remove('open'));
    
    if (!isOpen) {
        acc.classList.add('open');
        acc.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function openWeek(idx) {
    toggleAccordion(idx);
}

function renderResources(resources) {
    const grid = $('resourcesGrid');
    grid.innerHTML = '';
    resources.forEach(cat => {
        const card = document.createElement('div');
        card.className = 'resource-card';
        card.innerHTML = `
            <div class="resource-cat">${escapeHtml(cat.category)}</div>
            <ul class="resource-list">
                ${(cat.items || []).map(item => `
                    <li><a href="${item.url || '#'}" target="_blank">${escapeHtml(item.name)}</a></li>
                `).join('')}
            </ul>
        `;
        grid.appendChild(card);
    });
}

// ────── Refinement Chat (Sidebar Sidebar) ──────

function sendSuggestion(btn) {
    $('chatInput').value = btn.textContent;
    sendChatMessage();
}

function chatKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const msg = $('chatInput').value.trim();
    if (!msg || !currentPlan) return;

    try {
        showLoader('Refining plan...');
        $('chatInput').value = '';
        
        // Pass the CURRENT editable state back to server
        const data = await api('/refine', {
            goal: currentGoal,
            plan: currentPlan,
            message: msg
        });

        if (data.success && data.plan) {
            currentPlan = data.plan;
            currentEvents = data.events || [];
            timelineUnit = data.timeline_unit || 'Week';
            renderFullPlan(currentPlan);
            renderEvents(currentEvents);
        } else {
            alert(data.message || 'Could not update plan.');
        }
    } catch (err) {
        alert('Chat error: ' + err.message);
    } finally {
        hideLoader();
    }
}

// ────── Calendar & Reset ──────

async function resetAll() {
    await api('/reset').catch(() => {});
    location.reload();
}

function openCalendarModal() { $('calendarModal').classList.add('active'); }
function closeCalendarModal() { $('calendarModal').classList.remove('active'); }

function exportCalendar() {
    const startStr = $('calendarStartDate').value;
    if (!startStr) { alert('Select a start date'); return; }
    
    // Reference the existing ICS generation logic (collapsed for brevity)
    generateAndDownloadICS(currentPlan, new Date(startStr));
    closeCalendarModal();
}

function generateAndDownloadICS(plan, startDate) {
    const lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//GoalAgent//EN',
        'METHOD:PUBLISH'
    ];

    plan.timeline.forEach((w, wIdx) => {
        const weekStart = new Date(startDate);
        weekStart.setDate(weekStart.getDate() + (wIdx * 7));

        (w.topics || []).forEach((t, tIdx) => {
            const evDate = new Date(weekStart);
            evDate.setDate(evDate.getDate() + Math.min(tIdx, 4)); // Spread Mon-Fri
            
            const start = evDate.toISOString().replace(/-|:|\.\d+/g, '').slice(0, 15) + 'Z';
            const end = new Date(evDate.getTime() + 2*3600*1000).toISOString().replace(/-|:|\.\d+/g, '').slice(0, 15) + 'Z';

            lines.push('BEGIN:VEVENT');
            lines.push(`SUMMARY:${t.name}`);
            lines.push(`DESCRIPTION:${t.description} | Resource: ${t.resource_url}`);
            lines.push(`DTSTART:${start}`);
            lines.push(`DTEND:${end}`);
            lines.push('END:VEVENT');
        });
    });

    lines.push('END:VCALENDAR');
    const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'roadmap.ics';
    a.click();
}

// ────── Events UI ──────

function renderEvents(events) {
    const container = $('eventsListInline');
    const section = $('eventsSection');
    if (!container || !section) return;
    
    container.innerHTML = '';

    const validEvents = (events || []).filter(e => e.title);
    if (validEvents.length > 0) {
        show(section);
    } else {
        hide(section);
        return;
    }

    validEvents.forEach((ev, idx) => {
        const card = document.createElement('div');
        card.className = 'event-suggestion-card'; // Re-use styles
        card.style.background = 'white';
        
        const typeClass = (ev.type || 'Online').toLowerCase().replace(' ', '-');
        
        card.innerHTML = `
            <div class="event-badge ${typeClass}">${escapeHtml(ev.type || 'Online')}</div>
            <div class="event-name" style="font-size: 1rem;">${escapeHtml(ev.title)}</div>
            <div class="event-meta" style="font-size: 0.75rem; margin-bottom: 8px;">
                <span>📅 ${escapeHtml(ev.date)}</span> &middot; <span>🏢 ${escapeHtml(ev.organizer)}</span>
            </div>
            <div class="event-desc" style="font-size: 0.85rem; margin-bottom: 12px;">${escapeHtml(ev.summary)}</div>
            <div class="event-footer-actions">
                <button class="event-action-btn btn-add-cal" style="padding: 6px 12px; font-size: 0.75rem;" onclick="addEventToCalendar(${idx})">
                    Add to Cal
                </button>
                <a href="${ev.url || '#'}" target="_blank" class="event-action-btn btn-visit" style="padding: 6px 12px; font-size: 0.75rem;">
                    Details ↗
                </a>
            </div>
        `;
        container.appendChild(card);
    });
}

function addEventToCalendar(idx) {
    const ev = currentEvents[idx];
    if (!ev) return;

    // Estimate a date if it's just a string like "October 2026"
    let eventDate = new Date();
    if (ev.date && ev.date.includes('202')) {
        const parsed = Date.parse(ev.date);
        if (!isNaN(parsed)) eventDate = new Date(parsed);
    }

    const lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//GoalAgent//EN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        `SUMMARY:${ev.title}`,
        `DESCRIPTION:${ev.summary}\\n\\nOrganizer: ${ev.organizer}\\n\\nLink: ${ev.url}`,
        `DTSTART:${eventDate.toISOString().replace(/-|:|\.\d+/g, '').slice(0, 15)}Z`,
        `DTEND:${new Date(eventDate.getTime() + 2*3600*1000).toISOString().replace(/-|:|\.\d+/g, '').slice(0, 15)}Z`,
        'END:VEVENT',
        'END:VCALENDAR'
    ];

    const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${ev.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.ics`;
    a.click();
}

// ────── Utils ──────
function escapeHtml(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
