/**
 * KDTechX Enterprise Assessment Workspace & Engine
 * High-precision exam workspace, progressive persistence, server-authoritative timer,
 * keyboard accessibility, and atomic evaluation submission.
 */

window.KDTechXQuiz = (function() {
  'use strict';

  let config = {
    quizId: null,
    attemptId: null,
    remainingSeconds: 0,
    totalQuestions: 0,
    submitUrl: '',
    saveAnswerUrl: '',
    csrfToken: '',
    storageKey: '',
    reviewKey: ''
  };

  let timerInterval = null;
  let currentQuestionIndex = 0;
  let reviewIndices = new Set();
  let answeredQuestions = new Map(); // questionName -> optionValue
  let isSubmitting = false;

  function init(options) {
    config = { ...config, ...options };
    config.storageKey = `kdtechx_quiz_attempt_${config.attemptId}_answers`;
    config.reviewKey = `kdtechx_quiz_attempt_${config.attemptId}_reviews`;
    config.csrfToken = getCsrfToken();

    restoreReviews();
    restoreAnswers();
    setupOptionListeners();
    setupNavigationListeners();
    setupKeyboardShortcuts();
    setupNetworkListeners();
    formatCodeSnippets();
    startTimer();

    // Initial state render
    updateQuestionView(0);
    updateMetricsAndPalettes();
  }

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  /* --------------------------------------------------------------------------
     TIMER LOGIC (Server-Authoritative, visual on client)
     -------------------------------------------------------------------------- */
  function startTimer() {
    const capsuleEl = document.getElementById('quiz-timer-capsule');
    const displayEl = document.getElementById('timer-display');
    if (!displayEl) return;

    function formatTime(totalSecs) {
      const hrs = Math.floor(totalSecs / 3600);
      const mins = Math.floor((totalSecs % 3600) / 60);
      const secs = totalSecs % 60;
      if (hrs > 0) {
        return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      }
      return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    function renderTick() {
      if (config.remainingSeconds <= 0) {
        clearInterval(timerInterval);
        displayEl.textContent = '00:00';
        if (capsuleEl) {
          capsuleEl.className = 'kd-assess-timer-capsule is-critical';
        }
        if (window.KDTechXToast) {
          window.KDTechXToast.show('Assessment deadline reached. Securing final evaluation...', 'danger');
        }
        submitQuiz(true);
        return;
      }

      displayEl.textContent = formatTime(config.remainingSeconds);

      // Urgency state styling
      if (capsuleEl) {
        if (config.remainingSeconds < 60) {
          capsuleEl.className = 'kd-assess-timer-capsule is-critical';
        } else if (config.remainingSeconds < 300) {
          capsuleEl.className = 'kd-assess-timer-capsule is-warning';
        } else {
          capsuleEl.className = 'kd-assess-timer-capsule';
        }
      }

      config.remainingSeconds--;
    }

    renderTick();
    timerInterval = setInterval(renderTick, 1000);
  }

  /* --------------------------------------------------------------------------
     ANSWER SELECTION & PERSISTENCE
     -------------------------------------------------------------------------- */
  function setupOptionListeners() {
    const options = document.querySelectorAll('.kd-assessment-option');
    options.forEach(opt => {
      opt.addEventListener('click', function(e) {
        handleOptionSelect(this);
      });

      // Keyboard accessible selection
      opt.addEventListener('keydown', function(e) {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          handleOptionSelect(this);
        }
      });
    });
  }

  function handleOptionSelect(optionElement) {
    const input = optionElement.querySelector('.kd-native-radio');
    if (!input || input.disabled) return;

    input.checked = true;

    // Deselect siblings in the same question container
    const questionCard = optionElement.closest('.kd-question-surface');
    if (questionCard) {
      questionCard.querySelectorAll('.kd-assessment-option').forEach(el => {
        el.classList.remove('is-selected');
        el.setAttribute('aria-checked', 'false');
      });
    }

    optionElement.classList.add('is-selected');
    optionElement.setAttribute('aria-checked', 'true');

    // Register answered state
    answeredQuestions.set(input.name, input.value);
    persistAnswersLocally();

    // Trigger progressive backend autosave if snapshot ID is known
    const snapId = input.getAttribute('data-snap-id');
    if (snapId && config.saveAnswerUrl) {
      dispatchProgressiveSave(snapId, input.value);
    } else {
      showAutosaveStatus('saved');
    }

    updateMetricsAndPalettes();
  }

  function persistAnswersLocally() {
    try {
      const obj = Object.fromEntries(answeredQuestions);
      localStorage.setItem(config.storageKey, JSON.stringify(obj));
    } catch (e) {
      console.warn('LocalStorage unavailable for answer caching:', e);
    }
  }

  function restoreAnswers() {
    // 1. First restore answers passed directly by server from attempt snapshots
    document.querySelectorAll('.kd-native-radio:checked').forEach(radio => {
      answeredQuestions.set(radio.name, radio.value);
      const opt = radio.closest('.kd-assessment-option');
      if (opt) {
        opt.classList.add('is-selected');
        opt.setAttribute('aria-checked', 'true');
      }
    });

    // 2. Supplement from localStorage if available (client session recovery)
    try {
      const raw = localStorage.getItem(config.storageKey);
      if (raw) {
        const saved = JSON.parse(raw);
        for (const [name, val] of Object.entries(saved)) {
          const radio = document.querySelector(`.kd-native-radio[name="${name}"][value="${val}"]`);
          if (radio) {
            radio.checked = true;
            answeredQuestions.set(name, val);
            const opt = radio.closest('.kd-assessment-option');
            if (opt) {
              opt.classList.add('is-selected');
              opt.setAttribute('aria-checked', 'true');
            }
          }
        }
      }
    } catch (e) {
      console.warn('Failed restoring local answer cache:', e);
    }
  }

  function dispatchProgressiveSave(snapshotId, selectedOption) {
    showAutosaveStatus('saving');

    fetch(config.saveAnswerUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': config.csrfToken
      },
      body: JSON.stringify({
        snapshot_id: snapshotId,
        selected_option: selectedOption
      })
    })
    .then(res => res.json())
    .then(data => {
      showAutosaveStatus('saved');
    })
    .catch(err => {
      console.warn('Progressive save sync warning (local cache active):', err);
      showAutosaveStatus('offline');
    });
  }

  function showAutosaveStatus(state) {
    const indicators = document.querySelectorAll('.kd-autosave-indicator');
    indicators.forEach(el => {
      const label = el.querySelector('.kd-autosave-label');
      el.classList.remove('is-saving', 'is-offline');

      if (state === 'saving') {
        el.classList.add('is-saving');
        if (label) label.textContent = 'Saving...';
      } else if (state === 'offline') {
        el.classList.add('is-offline');
        if (label) label.textContent = 'Cached locally';
      } else {
        if (label) label.textContent = 'Auto-saved';
      }
    });
  }

  /* --------------------------------------------------------------------------
     REVIEW LOGIC (Mark for later review)
     -------------------------------------------------------------------------- */
  function toggleReview(index = null) {
    const targetIdx = index !== null ? index : currentQuestionIndex;
    if (reviewIndices.has(targetIdx)) {
      reviewIndices.delete(targetIdx);
    } else {
      reviewIndices.add(targetIdx);
    }

    persistReviews();
    updateReviewButtons();
    updateMetricsAndPalettes();
  }

  function persistReviews() {
    try {
      localStorage.setItem(config.reviewKey, JSON.stringify(Array.from(reviewIndices)));
    } catch (e) {}
  }

  function restoreReviews() {
    try {
      const raw = localStorage.getItem(config.reviewKey);
      if (raw) {
        const arr = JSON.parse(raw);
        reviewIndices = new Set(arr);
      }
    } catch (e) {}
  }

  function updateReviewButtons() {
    const isMarked = reviewIndices.has(currentQuestionIndex);

    // Desktop button
    const reviewBtn = document.getElementById('btn-mark-review');
    if (reviewBtn) {
      reviewBtn.classList.toggle('is-marked', isMarked);
      reviewBtn.innerHTML = isMarked
        ? '<i class="bi bi-bookmark-fill"></i> Marked for Review'
        : '<i class="bi bi-bookmark"></i> Mark for Review';
    }

    // Mobile button
    const mobileReviewBtn = document.getElementById('mobile-btn-review');
    if (mobileReviewBtn) {
      mobileReviewBtn.classList.toggle('is-marked', isMarked);
      mobileReviewBtn.innerHTML = isMarked
        ? '<i class="bi bi-bookmark-fill text-warning"></i> Review'
        : '<i class="bi bi-bookmark"></i> Review';
    }

    // Question surface review tag
    const currentCard = document.querySelector(`.kd-question-surface[data-question-index="${currentQuestionIndex}"]`);
    if (currentCard) {
      const tag = currentCard.querySelector('.chip-review-tag');
      if (tag) {
        tag.style.display = isMarked ? 'inline-flex' : 'none';
      }
    }
  }

  /* --------------------------------------------------------------------------
     QUESTION WORKSPACE NAVIGATION
     -------------------------------------------------------------------------- */
  function updateQuestionView(targetIndex) {
    const cards = document.querySelectorAll('.kd-question-surface');
    if (!cards.length) return;

    if (targetIndex < 0) targetIndex = 0;
    if (targetIndex >= cards.length) targetIndex = cards.length - 1;

    currentQuestionIndex = targetIndex;

    cards.forEach((card, i) => {
      card.style.display = (i === currentQuestionIndex) ? 'block' : 'none';
    });

    // Update command bar question counter
    const hdrCurrent = document.getElementById('hdr-current-q');
    if (hdrCurrent) {
      hdrCurrent.textContent = String(currentQuestionIndex + 1).padStart(2, '0');
    }

    // Update Previous / Next button states
    const prevBtns = document.querySelectorAll('.kd-nav-btn-prev, .kd-mobile-btn-prev');
    prevBtns.forEach(btn => {
      btn.disabled = (currentQuestionIndex === 0);
    });

    const isLast = (currentQuestionIndex === cards.length - 1);
    const nextBtnDesktop = document.getElementById('quiz-next-btn');
    if (nextBtnDesktop) {
      if (isLast) {
        nextBtnDesktop.innerHTML = 'Review & Submit <i class="bi bi-send-check"></i>';
        nextBtnDesktop.className = 'kd-nav-btn kd-nav-btn-submit';
      } else {
        nextBtnDesktop.innerHTML = 'Next Question <i class="bi bi-chevron-right"></i>';
        nextBtnDesktop.className = 'kd-nav-btn kd-nav-btn-next';
      }
    }

    const nextBtnMobile = document.getElementById('mobile-btn-next');
    if (nextBtnMobile) {
      if (isLast) {
        nextBtnMobile.innerHTML = 'Review <i class="bi bi-send"></i>';
      } else {
        nextBtnMobile.innerHTML = 'Next <i class="bi bi-chevron-right"></i>';
      }
    }

    updateReviewButtons();
    updateMetricsAndPalettes();

    // Scroll workspace smoothly to top on question change
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goToQuestion(index) {
    updateQuestionView(index);

    // If mobile bottom sheet offcanvas is open, close it
    const offcanvasEl = document.getElementById('mobileQuestionSheet');
    if (offcanvasEl && typeof bootstrap !== 'undefined') {
      const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
      if (bsOffcanvas) bsOffcanvas.hide();
    }
  }

  function updateMetricsAndPalettes() {
    const total = config.totalQuestions || document.querySelectorAll('.kd-question-surface').length;
    let answeredCount = 0;

    // Evaluate answered cards
    document.querySelectorAll('.kd-question-surface').forEach((card, idx) => {
      const hasAnswer = !!card.querySelector('.kd-native-radio:checked');
      if (hasAnswer) answeredCount++;

      const isCurrent = (idx === currentQuestionIndex);
      const isReview = reviewIndices.has(idx);

      // Update Desktop Matrix Pills
      const pills = document.querySelectorAll(`.kd-matrix-pill[data-question-index="${idx}"]`);
      pills.forEach(pill => {
        pill.classList.toggle('is-current', isCurrent);
        pill.classList.toggle('is-answered', hasAnswer);
        pill.classList.toggle('is-review', isReview);
      });
    });

    const unansweredCount = total - answeredCount;
    const reviewCount = reviewIndices.size;
    const pct = total > 0 ? Math.round((answeredCount / total) * 100) : 0;

    // Update Header progress bar
    const barFill = document.getElementById('hdr-progress-fill');
    if (barFill) barFill.style.width = `${pct}%`;

    const barAnsweredBadge = document.getElementById('hdr-answered-count');
    if (barAnsweredBadge) barAnsweredBadge.textContent = answeredCount;

    // Update Rail KPI counters
    const kpiAns = document.getElementById('kpi-answered-count');
    const kpiUnans = document.getElementById('kpi-unanswered-count');
    const kpiRev = document.getElementById('kpi-review-count');

    if (kpiAns) kpiAns.textContent = answeredCount;
    if (kpiUnans) kpiUnans.textContent = unansweredCount;
    if (kpiRev) kpiRev.textContent = reviewCount;

    // Update Mobile trigger button label
    const mobilePaletteBtn = document.getElementById('mobile-btn-palette');
    if (mobilePaletteBtn) {
      mobilePaletteBtn.innerHTML = `<i class="bi bi-grid-3x3-gap"></i> ${String(currentQuestionIndex + 1).padStart(2, '0')}/${String(total).padStart(2, '0')}`;
    }
  }

  /* --------------------------------------------------------------------------
     NAVIGATION LISTENERS & SHORTCUTS
     -------------------------------------------------------------------------- */
  function setupNavigationListeners() {
    // Previous Question
    const handlePrev = () => updateQuestionView(currentQuestionIndex - 1);
    document.querySelectorAll('.kd-nav-btn-prev, .kd-mobile-btn-prev').forEach(btn => {
      btn.addEventListener('click', handlePrev);
    });

    // Next Question or Review Trigger
    const handleNext = () => {
      const total = config.totalQuestions || document.querySelectorAll('.kd-question-surface').length;
      if (currentQuestionIndex >= total - 1) {
        showReviewModal();
      } else {
        updateQuestionView(currentQuestionIndex + 1);
      }
    };
    document.querySelectorAll('.kd-nav-btn-next, #mobile-btn-next, #quiz-next-btn').forEach(btn => {
      btn.addEventListener('click', handleNext);
    });

    // Mark for Review toggles
    const handleReview = () => toggleReview();
    const btnReview = document.getElementById('btn-mark-review');
    if (btnReview) btnReview.addEventListener('click', handleReview);
    const mobileBtnReview = document.getElementById('mobile-btn-review');
    if (mobileBtnReview) mobileBtnReview.addEventListener('click', handleReview);

    // Matrix Pill direct jumps
    document.addEventListener('click', e => {
      const pill = e.target.closest('.kd-matrix-pill, .kd-review-chip');
      if (pill && pill.hasAttribute('data-question-index')) {
        const idx = parseInt(pill.getAttribute('data-question-index'), 10);
        goToQuestion(idx);

        // If in review modal, hide it
        const reviewModalEl = document.getElementById('quizReviewModal');
        if (reviewModalEl && typeof bootstrap !== 'undefined') {
          const bsModal = bootstrap.Modal.getInstance(reviewModalEl);
          if (bsModal) bsModal.hide();
        }
      }
    });

    // Fullscreen Toggle
    const fsBtn = document.getElementById('btn-fullscreen-toggle');
    if (fsBtn) {
      fsBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      });
    }

    // Submit Triggers (Header button or action button)
    const topSubmit = document.getElementById('btn-submit-assessment-top');
    if (topSubmit) topSubmit.addEventListener('click', showReviewModal);
  }

  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', e => {
      // Ignore if user is typing in an input/textarea
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        updateQuestionView(currentQuestionIndex - 1);
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        const total = config.totalQuestions || document.querySelectorAll('.kd-question-surface').length;
        if (currentQuestionIndex < total - 1) {
          updateQuestionView(currentQuestionIndex + 1);
        }
      } else if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        toggleReview();
      } else if (['1', '2', '3', '4'].includes(e.key)) {
        const optionIndex = parseInt(e.key, 10) - 1;
        const currentCard = document.querySelector(`.kd-question-surface[data-question-index="${currentQuestionIndex}"]`);
        if (currentCard) {
          const options = currentCard.querySelectorAll('.kd-assessment-option');
          if (options[optionIndex]) {
            e.preventDefault();
            handleOptionSelect(options[optionIndex]);
          }
        }
      }
    });
  }

  function setupNetworkListeners() {
    window.addEventListener('offline', () => {
      showAutosaveStatus('offline');
      if (window.KDTechXToast) {
        window.KDTechXToast.show('Network interrupted. Your answers are preserved locally and will sync once reconnected.', 'warning');
      }
    });

    window.addEventListener('online', () => {
      showAutosaveStatus('saved');
      if (window.KDTechXToast) {
        window.KDTechXToast.show('Network re-established. Connection synchronized.', 'success');
      }
    });
  }

  /* --------------------------------------------------------------------------
     CODE SNIPPET PRETTIFIER
     -------------------------------------------------------------------------- */
  function formatCodeSnippets() {
    document.querySelectorAll('.kd-question-text').forEach(el => {
      const html = el.innerHTML;
      // Convert triple backticks ```code``` into styled dark code boxes if present
      if (html.includes('```')) {
        const formatted = html.replace(/```([a-zA-Z]*)\n([\s\S]*?)```/g, (match, lang, code) => {
          return `
            <div class="kd-code-block">
              <div class="kd-code-header">
                <span>${lang || 'Code Snippet'}</span>
                <span><i class="bi bi-code-slash"></i></span>
              </div>
              <pre class="kd-code-content"><code>${escapeHtml(code.trim())}</code></pre>
            </div>
          `;
        });
        el.innerHTML = formatted;
      }
    });
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /* --------------------------------------------------------------------------
     REVIEW & SUBMISSION CONFIRMATION MODAL
     -------------------------------------------------------------------------- */
  function showReviewModal() {
    const total = config.totalQuestions || document.querySelectorAll('.kd-question-surface').length;
    let answeredCount = 0;

    const chipsContainer = document.getElementById('modal-review-chips');
    if (chipsContainer) chipsContainer.innerHTML = '';

    document.querySelectorAll('.kd-question-surface').forEach((card, idx) => {
      const isAnswered = !!card.querySelector('.kd-native-radio:checked');
      if (isAnswered) answeredCount++;

      const isReview = reviewIndices.has(idx);

      if (chipsContainer) {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = `kd-review-chip ${isAnswered ? 'is-answered' : 'is-unanswered'} ${isReview ? 'is-review' : ''}`;
        chip.setAttribute('data-question-index', idx);
        chip.innerHTML = `Q${idx + 1} ${isReview ? '◆' : isAnswered ? '✓' : '•'}`;
        chipsContainer.appendChild(chip);
      }
    });

    const unansweredCount = total - answeredCount;
    const reviewCount = reviewIndices.size;

    // Update modal stat values
    const mTotal = document.getElementById('modal-stat-total');
    const mAns = document.getElementById('modal-stat-answered');
    const mUnans = document.getElementById('modal-stat-unanswered');
    const mRev = document.getElementById('modal-stat-review');

    if (mTotal) mTotal.textContent = total;
    if (mAns) mAns.textContent = answeredCount;
    if (mUnans) mUnans.textContent = unansweredCount;
    if (mRev) mRev.textContent = reviewCount;

    // Unanswered warning alert
    const warnAlert = document.getElementById('modal-unanswered-alert');
    const warnCountEl = document.getElementById('modal-alert-unanswered-count');
    if (warnAlert) {
      if (unansweredCount > 0) {
        warnAlert.style.display = 'flex';
        if (warnCountEl) warnCountEl.textContent = unansweredCount;
      } else {
        warnAlert.style.display = 'none';
      }
    }

    // Show modal via Bootstrap
    const modalEl = document.getElementById('quizReviewModal');
    if (modalEl && typeof bootstrap !== 'undefined') {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    } else {
      if (confirm(`Submit assessment now?\n\nAnswered: ${answeredCount}\nUnanswered: ${unansweredCount}`)) {
        submitQuiz(false);
      }
    }
  }

  function submitQuiz(forced = false) {
    if (isSubmitting) return;
    isSubmitting = true;

    if (timerInterval) clearInterval(timerInterval);

    // Clear local attempt cache upon authoritative submit
    try {
      localStorage.removeItem(config.storageKey);
      localStorage.removeItem(config.reviewKey);
    } catch (e) {}

    // Disable buttons and show loading spinner
    const finalizeBtn = document.getElementById('btn-confirm-finalize');
    if (finalizeBtn) {
      finalizeBtn.disabled = true;
      finalizeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Submitting Securely...';
    }

    const form = document.getElementById('quiz-submission-form');
    if (form) {
      if (forced) {
        const forcedInput = document.createElement('input');
        forcedInput.type = 'hidden';
        forcedInput.name = 'forced_timeout';
        forcedInput.value = '1';
        form.appendChild(forcedInput);
      }
      form.submit();
    }
  }

  return {
    init,
    submitQuiz,
    goToQuestion,
    toggleReview,
    showReviewModal
  };
})();
