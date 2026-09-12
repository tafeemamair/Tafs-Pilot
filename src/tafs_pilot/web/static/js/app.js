/**
 * Taf's Pilot - Autonomous Video Production Agent Console
 * Controller & State Machine
 */

class ProductionConsole {
  constructor() {
    this.state = 'IDLE'; // IDLE, PLANNING, AWAITING_HOOK_APPROVAL, HOOK_APPROVED, PRODUCING, AUDITING, REVISION_REQUIRED, REVISION_IN_PROGRESS, READY_FOR_REVIEW, DELIVERED
    this.projectData = null;
    this.selectedHook = null;
    this.autoStepTimer = null;
    this.stages = ['UNDERSTAND', 'PLAN', 'ASK', 'PRODUCE', 'INSPECT', 'CORRECT', 'DELIVER'];
    this.currentStageIndex = 0; // 0 to 6
    this.completedStages = new Set();
    
    this.initElements();
    this.bindEvents();
    this.fetchProjectData();
  }

  initElements() {
    // Buttons
    this.btnStart = document.getElementById('btn-start-production');
    this.btnReset = document.getElementById('btn-reset');
    this.btnJumpDefect = document.getElementById('btn-jump-defect');
    this.btnApprove = document.getElementById('btn-approve-video');
    this.btnViewReport = document.getElementById('btn-view-report');
    this.btnCloseModal = document.getElementById('btn-close-modal');

    // Panels & containers
    this.activityFeed = document.getElementById('activity-feed');
    this.stagesTracker = document.getElementById('stages-tracker');
    this.videoElement = document.getElementById('preview-video');
    this.videoPlaceholder = document.getElementById('video-placeholder');
    this.videoScanning = document.getElementById('video-scanning');
    this.videoFrameOuter = document.getElementById('video-frame-outer');
    this.badgeLatest = document.getElementById('badge-latest');
    this.badgeDefect = document.getElementById('badge-defect');
    this.badgeSpec = document.getElementById('badge-spec');
    this.telemetryBar = document.getElementById('telemetry-bar');
    this.deliveryActions = document.getElementById('delivery-actions');
    this.reportModal = document.getElementById('report-modal');
    this.reportCode = document.getElementById('report-code');
    this.briefLockNotice = document.getElementById('brief-lock-notice');
    this.revisionTrail = document.getElementById('revision-trail');

    // Input fields
    this.topicInput = document.getElementById('brief-topic');
    this.audienceInput = document.getElementById('brief-audience');
    this.goalInput = document.getElementById('brief-goal');
    this.toneInput = document.getElementById('brief-tone');
    this.durationInput = document.getElementById('brief-duration');
    this.platformInput = document.getElementById('brief-platform');
  }

  bindEvents() {
    this.btnStart.addEventListener('click', () => this.startProduction());
    this.btnReset.addEventListener('click', () => this.resetConsole());
    this.btnJumpDefect.addEventListener('click', () => this.jumpToQCDefect());
    this.btnApprove.addEventListener('click', () => this.approveDeliverable());
    this.btnViewReport.addEventListener('click', () => this.showReportModal());
    this.btnCloseModal.addEventListener('click', () => this.hideReportModal());

    this.reportModal.addEventListener('click', (e) => {
      if (e.target === this.reportModal) this.hideReportModal();
    });
  }

  async fetchProjectData() {
    try {
      const res = await fetch('/api/project/74ed7661');
      if (res.ok) {
        this.projectData = await res.json();
      }
    } catch (e) {
      console.warn('Using offline project state fallback:', e);
    }
  }

  // =========================================================================
  // Timeline Stages & Navigation
  // =========================================================================
  updateTimeline(activeStageName, completedStageNames = []) {
    const stageNodes = this.stagesTracker.querySelectorAll('.stage-node');
    stageNodes.forEach((node) => {
      const name = node.getAttribute('data-stage');
      const icon = node.querySelector('.stage-icon');

      const isCompleted = completedStageNames.includes(name);
      const isActive = name === activeStageName;

      if (isCompleted && isActive) {
        node.className = 'stage-node completed active';
        icon.innerHTML = '✓';
      } else if (isCompleted) {
        node.className = 'stage-node completed';
        icon.innerHTML = '✓';
      } else if (isActive) {
        node.className = 'stage-node active';
        icon.innerHTML = '●';
      } else {
        node.className = 'stage-node muted';
        icon.innerHTML = '○';
      }
    });
  }

  // =========================================================================
  // Activity Feed Logging
  // =========================================================================
  addActivityItem({ title, desc, status = 'success', extraHtml = '' }) {
    const item = document.createElement('div');
    item.className = 'activity-item';

    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];

    let iconHtml = '✓';
    if (status === 'pending') iconHtml = '⚡';
    if (status === 'warning') iconHtml = '⚠';

    item.innerHTML = `
      <div class="activity-status-icon ${status}">${iconHtml}</div>
      <div class="activity-body">
        <div class="activity-header-line">
          <span class="activity-title">${title}</span>
          <span class="activity-timestamp">${timeStr}</span>
        </div>
        <p class="activity-desc">${desc}</p>
        ${extraHtml}
      </div>
    `;

    this.activityFeed.appendChild(item);
    this.activityFeed.scrollTop = this.activityFeed.scrollHeight;
    return item;
  }

  // =========================================================================
  // State Machine Transitions
  // =========================================================================
  startProduction() {
    if (this.state !== 'IDLE') return;

    this.state = 'PLANNING';
    this.btnStart.disabled = true;
    this.briefLockNotice.style.display = 'flex';
    this.briefLockNotice.textContent = '🔒 Brief locked. Taf’s Pilot is executing production.';

    // Stage 1: UNDERSTAND
    this.updateTimeline('UNDERSTAND');
    this.addActivityItem({
      title: 'Brief understood',
      desc: `Turning brief "${this.topicInput.value}" into a structured production specification.`,
      status: 'success',
    });

    setTimeout(() => {
      // Stage 2: PLAN
      this.updateTimeline('PLAN', ['UNDERSTAND']);
      this.addActivityItem({
        title: 'Production plan created',
        desc: 'Narrative structure, scene breakdowns, visuals and speech pacing mapped.',
        status: 'success',
      });

      setTimeout(() => {
        // Stage 3: ASK (Hook Formulation)
        this.renderHookProposals();
      }, 1200);
    }, 1200);
  }

  renderHookProposals() {
    this.state = 'AWAITING_HOOK_APPROVAL';
    this.updateTimeline('ASK', ['UNDERSTAND', 'PLAN']);

    const hooks = this.projectData?.hooks || [
      { id: 'h1', number: '01', text: "The best senior engineers don't write more code. They delete it.", recommended: true, angle: 'Counterintuitive senior engineering philosophy' },
      { id: 'h2', number: '02', text: 'Juniors count lines committed. Seniors count problems prevented.', recommended: false, angle: 'Direct metric contrast: activity vs impact' },
      { id: 'h3', number: '03', text: 'The fastest code in production is the code you never wrote.', recommended: false, angle: 'Architectural simplicity and performance' }
    ];

    let hooksHtml = '<div class="hook-cards-container">';
    hooks.forEach((h) => {
      hooksHtml += `
        <div class="hook-card ${h.recommended ? 'recommended' : ''}">
          <div class="hook-top-bar">
            <span class="hook-number">HOOK ${h.number}</span>
            ${h.recommended ? '<span class="recommended-pill">Recommended</span>' : ''}
          </div>
          <div class="hook-text">"${h.text}"</div>
          <div class="hook-angle">${h.angle}</div>
          <button class="btn-select-hook" data-hook-id="${h.id}" data-hook-text="${h.text}">Select Hook</button>
        </div>
      `;
    });
    hooksHtml += '</div>';

    this.addActivityItem({
      title: 'Hooks generated',
      desc: '3 creative directions formulated. Choose the hook Taf’s Pilot should produce:',
      status: 'pending',
      extraHtml: hooksHtml,
    });

    // Attach click listeners to hook buttons
    const hookButtons = this.activityFeed.querySelectorAll('.btn-select-hook');
    hookButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const text = e.target.getAttribute('data-hook-text');
        this.selectHook(text);
      });
    });
  }

  selectHook(chosenHookText) {
    if (this.state !== 'AWAITING_HOOK_APPROVAL') return;

    this.selectedHook = chosenHookText;
    this.state = 'HOOK_APPROVED';

    // Disable all hook buttons
    this.activityFeed.querySelectorAll('.btn-select-hook').forEach((b) => (b.disabled = true));

    this.addActivityItem({
      title: 'Creative direction approved',
      desc: `Creator selected: "${chosenHookText}". Proceeding directly into autonomous production.`,
      status: 'success',
    });

    setTimeout(() => {
      this.executeProduction();
    }, 1000);
  }

  executeProduction() {
    this.state = 'PRODUCING';
    this.updateTimeline('PRODUCE', ['UNDERSTAND', 'PLAN', 'ASK']);

    // Video preview shows rendering scanline
    this.videoPlaceholder.style.display = 'none';
    this.videoScanning.style.display = 'flex';

    const subtasksHtml = `
      <div class="production-subtasks">
        <div class="subtask-item active" id="task-vo">● Voiceover (AWS Polly)</div>
        <div class="subtask-item" id="task-vis">○ Visual B-Roll (Procedural/Titan)</div>
        <div class="subtask-item" id="task-cap">○ Burn Subtitles (SRT)</div>
        <div class="subtask-item" id="task-asm">○ Composite MP4 (FFmpeg)</div>
      </div>
    `;

    this.addActivityItem({
      title: 'Taf’s Pilot is producing deliverable...',
      desc: 'Executing multi-track media pipeline: speech synthesis, 1080x1920 visuals, and FFmpeg assembly.',
      status: 'pending',
      extraHtml: subtasksHtml,
    });

    setTimeout(() => {
      const taskVo = document.getElementById('task-vo');
      if (taskVo) { taskVo.className = 'subtask-item done'; taskVo.textContent = '✓ Voiceover (AWS Polly)'; }
      const taskVis = document.getElementById('task-vis');
      if (taskVis) { taskVis.className = 'subtask-item active'; taskVis.textContent = '● Visual B-Roll (Procedural/Titan)'; }
    }, 800);

    setTimeout(() => {
      const taskVis = document.getElementById('task-vis');
      if (taskVis) { taskVis.className = 'subtask-item done'; taskVis.textContent = '✓ Visual B-Roll (Procedural/Titan)'; }
      const taskCap = document.getElementById('task-cap');
      if (taskCap) { taskCap.className = 'subtask-item active'; taskCap.textContent = '● Burn Subtitles (SRT)'; }
    }, 1600);

    setTimeout(() => {
      const taskCap = document.getElementById('task-cap');
      if (taskCap) { taskCap.className = 'subtask-item done'; taskCap.textContent = '✓ Burn Subtitles (SRT)'; }
      const taskAsm = document.getElementById('task-asm');
      if (taskAsm) { taskAsm.className = 'subtask-item done'; taskAsm.textContent = '✓ Composite MP4 (FFmpeg)'; }
    }, 2400);

    setTimeout(() => {
      this.triggerQCInspection();
    }, 3200);
  }

  // =========================================================================
  // The Killer Demo Moment: QC Failure & Autonomous Self-Correction
  // =========================================================================
  triggerQCInspection() {
    this.state = 'INSPECTING';
    this.updateTimeline('INSPECT', ['UNDERSTAND', 'PLAN', 'ASK', 'PRODUCE']);

    // Display defect cut in player
    this.videoScanning.style.display = 'none';
    this.videoFrameOuter?.classList.add('has-video');
    this.videoElement.src = this.projectData?.defect_video_url || '/artifacts/74ed7661/revisions/pre_revision_1.mp4';
    this.videoElement.style.display = 'block';
    this.videoElement.muted = true;
    this.videoElement.play().catch(() => {});
    this.badgeDefect.style.display = 'block';
    this.badgeLatest.style.display = 'none';
    if (this.badgeSpec) this.badgeSpec.style.display = 'block';

    // Highlight timeline failure
    const inspectNode = this.stagesTracker.querySelector('[data-stage="INSPECT"]');
    if (inspectNode) inspectNode.className = 'stage-node active';

    // Activity: QC Failure Banner + Agent Decision Card
    const defectBannerHtml = `
      <div class="qc-defect-banner">
        <div class="defect-header">
          <span>⚠ REVISION REQUIRED</span>
          <span style="font-family: var(--font-mono); font-size: 10px; color: var(--accent-amber);">AUDIT #2</span>
        </div>
        <div class="defect-desc">Missing active audio narration stream in Scene 4.</div>
      </div>
      <div class="agent-decision-card" style="margin-top: 10px;">
        <div class="agent-header-row">
          <span class="agent-signature">TAF'S PILOT</span>
          <span class="correcting-pill" id="agent-decision-pill"><div class="spinner"></div> Correcting automatically...</span>
        </div>
        <p class="agent-speech">
          "I found the issue. The final cut is missing its active audio narration stream.
          I am regenerating the voiceover track, re-rendering affected scenes, and reassembling the video."
        </p>
      </div>
    `;

    this.addActivityItem({
      title: 'Automated QC Inspection Complete',
      desc: 'FFprobe multi-stream compliance check detected an audible defect.',
      status: 'warning',
      extraHtml: defectBannerHtml,
    });

    // Update revision trail
    this.revisionTrail.innerHTML = `
      <span class="trail-step fail">Initial cut (QC failed)</span>
      <span>→</span>
      <span class="trail-step active">Regenerating audio...</span>
    `;

    // Autonomous self-correction step
    setTimeout(() => {
      this.executeAutonomousCorrection();
    }, 2800);
  }

  executeAutonomousCorrection() {
    this.state = 'CORRECTING';
    this.updateTimeline('CORRECT', ['UNDERSTAND', 'PLAN', 'ASK', 'PRODUCE', 'INSPECT']);

    // Ensure status pill displays "Correcting automatically..." during revision in progress
    const decisionPill = document.getElementById('agent-decision-pill');
    if (decisionPill) {
      decisionPill.className = 'correcting-pill';
      decisionPill.innerHTML = '<div class="spinner"></div> Correcting automatically...';
    }

    this.correctionActivityItem = this.addActivityItem({
      title: 'Autonomous Correction in Progress',
      desc: 'Regenerating audio scene #4 via synthesis engine → Reassembling video deliverable → Re-running QC validation.',
      status: 'pending',
    });

    setTimeout(() => {
      this.finishQCAndDeliver();
    }, 2600);
  }

  finishQCAndDeliver() {
    this.state = 'READY_FOR_REVIEW';
    this.updateTimeline('DELIVER', ['UNDERSTAND', 'PLAN', 'ASK', 'PRODUCE', 'INSPECT', 'CORRECT']);

    // Update autonomous decision card pill: "Correction completed · QC verified"
    const decisionPill = document.getElementById('agent-decision-pill');
    if (decisionPill) {
      decisionPill.className = 'correcting-pill completed';
      decisionPill.innerHTML = '<span class="pill-check">✓</span> Correction completed · QC verified';
    }

    // Update autonomous correction activity item in feed: "Autonomous Correction Complete"
    if (this.correctionActivityItem) {
      const icon = this.correctionActivityItem.querySelector('.activity-status-icon');
      const title = this.correctionActivityItem.querySelector('.activity-title');
      const desc = this.correctionActivityItem.querySelector('.activity-desc');
      if (icon) {
        icon.className = 'activity-status-icon success';
        icon.textContent = '✓';
      }
      if (title) title.textContent = 'Autonomous Correction Complete';
      if (desc) desc.textContent = 'Voiceover regenerated → video reassembled → QC re-run and passed.';
    }

    // Video preview switches to pristine final video
    this.videoFrameOuter?.classList.add('has-video');
    this.videoElement.pause();
    this.videoElement.src = this.projectData?.final_video_url || '/artifacts/74ed7661/final.mp4';
    this.videoElement.muted = true;
    this.videoElement.addEventListener('loadedmetadata', () => {
      this.videoElement.currentTime = 0;
      this.videoElement.pause();
    }, { once: true });
    this.videoElement.load();
    this.badgeDefect.style.display = 'none';
    this.badgeLatest.style.display = 'flex';
    if (this.badgeSpec) this.badgeSpec.style.display = 'block';

    // Show telemetry
    this.telemetryBar.style.display = 'grid';

    // Show QC Pass Banner in Activity Feed
    const qcPassHtml = `
      <div class="qc-passed-card">
        <div class="qc-passed-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
          QC PASSED — Revision #1 Validated
        </div>
        <div class="qc-checklist">
          <div class="qc-check-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Video stream (h264 1080x1920)
          </div>
          <div class="qc-check-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Audio stream (aac active)
          </div>
          <div class="qc-check-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Runtime: 18.07s (tolerance OK)
          </div>
          <div class="qc-check-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Captions aligned (3 beats)
          </div>
        </div>
      </div>
    `;

    this.addActivityItem({
      title: 'Production Complete',
      desc: 'Taf’s Pilot successfully corrected the defect and verified all quality gates.',
      status: 'success',
      extraHtml: qcPassHtml,
    });

    // Update revision trail
    this.revisionTrail.innerHTML = `
      <span class="trail-step">Initial cut</span>
      <span>→</span>
      <span class="trail-step fail">QC failed</span>
      <span>→</span>
      <span class="trail-step">Audio regenerated</span>
      <span>→</span>
      <span class="trail-step pass">Final cut (QC passed)</span>
    `;

    // Show delivery actions
    this.deliveryActions.style.display = 'flex';
  }

  approveDeliverable() {
    this.state = 'DELIVERED';
    // All 7 stages completed including DELIVER (active/completed)
    this.updateTimeline('DELIVER', ['UNDERSTAND', 'PLAN', 'ASK', 'PRODUCE', 'INSPECT', 'CORRECT', 'DELIVER']);

    // Update autonomous decision card pill: "Production complete · Ready for release"
    const decisionPill = document.getElementById('agent-decision-pill');
    if (decisionPill) {
      decisionPill.className = 'correcting-pill delivered';
      decisionPill.innerHTML = '<span class="pill-check">✓</span> Production complete · Ready for release';
    }

    this.btnApprove.disabled = true;
    this.btnApprove.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
      ✓ Video Approved for Release
    `;
    this.btnApprove.style.background = '#059669';

    this.addActivityItem({
      title: 'Creator Sign-off Recorded',
      desc: 'Deliverable approved by creator.',
      status: 'success',
    });
  }

  jumpToQCDefect() {
    // Fast-forward directly to the killer demo moment
    this.resetConsole();
    this.state = 'HOOK_APPROVED';
    this.selectedHook = "The best senior engineers don't write more code. They delete it.";
    this.btnStart.disabled = true;
    this.briefLockNotice.style.display = 'flex';

    this.addActivityItem({
      title: 'Demo Fast-Forward: Creative Direction',
      desc: 'Selected: "The best senior engineers don\'t write more code. They delete it." Jumping straight to inspection defect...',
      status: 'success',
    });

    setTimeout(() => {
      this.triggerQCInspection();
    }, 400);
  }

  resetConsole() {
    this.state = 'IDLE';
    this.selectedHook = null;
    this.btnStart.disabled = false;
    this.btnApprove.disabled = false;
    this.btnApprove.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
      Approve Final Video
    `;
    this.btnApprove.style.background = '';
    this.briefLockNotice.style.display = 'none';
    this.deliveryActions.style.display = 'none';
    this.telemetryBar.style.display = 'none';
    this.badgeDefect.style.display = 'none';
    this.badgeLatest.style.display = 'none';
    if (this.badgeSpec) this.badgeSpec.style.display = 'none';
    this.videoFrameOuter?.classList.remove('has-video');

    this.videoElement.pause();
    this.videoElement.style.display = 'none';
    this.videoScanning.style.display = 'none';
    this.videoPlaceholder.style.display = 'flex';

    this.activityFeed.innerHTML = '';
    this.updateTimeline('UNDERSTAND');

    this.revisionTrail.innerHTML = `
      <span class="trail-step">Initial cut</span>
      <span>→</span>
      <span class="trail-step">Final cut</span>
    `;
  }

  showReportModal() {
    const reportData = {
      project_id: this.projectData?.project_id || '74ed7661',
      qc_report: this.projectData?.qc || {},
      revision_decision: this.projectData?.revision_decision || {},
      audit_history: this.projectData?.audit_history || [],
      selected_hook: this.selectedHook || "The best senior engineers don't write more code. They delete it.",
    };

    this.reportCode.textContent = JSON.stringify(reportData, null, 2);
    this.reportModal.classList.add('show');
  }

  hideReportModal() {
    this.reportModal.classList.remove('show');
  }
}

// Instantiate on DOM load
document.addEventListener('DOMContentLoaded', () => {
  window.consoleApp = new ProductionConsole();
});
