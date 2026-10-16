/**
 * KDTechX AI Coding Tutor & Intelligent Doubt-Clearing Client
 * Integrates context-aware AI explanations, debugging, error analysis, and Q&A.
 */
(function () {
  'use strict';

  const tutorState = {
    isOpen: true,
    isLoading: false,
    conversationId: null,
    learningMode: 'intermediate',
    lastPayload: null,
    lastEndpoint: null
  };

  function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Safe Markdown Parser supporting bold, italics, headings, lists, inline code,
   * and fenced code blocks with Copy & Insert buttons.
   */
  function renderMarkdownSafe(mdText) {
    if (!mdText) return '';

    // First, extract fenced code blocks to prevent inner markdown processing
    const codeBlocks = [];
    let processed = mdText.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const idx = codeBlocks.length;
      codeBlocks.push({ lang: lang || 'code', code: code });
      return `@@CODE_BLOCK_${idx}@@`;
    });

    // Escape raw HTML in text
    processed = escapeHtml(processed);

    // Headers
    processed = processed.replace(/^### (.*$)/gim, '<h4 class="h6 fw-bold text-light mt-3 mb-1">$1</h4>');
    processed = processed.replace(/^## (.*$)/gim, '<h3 class="h6 fw-bold text-light mt-3 mb-1">$1</h3>');
    processed = processed.replace(/^# (.*$)/gim, '<h2 class="h6 fw-bold text-light mt-3 mb-1">$1</h2>');

    // Bold & Italics
    processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    processed = processed.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Inline code
    processed = processed.replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 rounded bg-dark text-info font-monospace">$1</code>');

    // Lists
    processed = processed.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
    processed = processed.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul class="ps-3 mb-2">$1</ul>');

    // Paragraph line breaks
    processed = processed.replace(/\n\n+/g, '</p><p>');
    processed = `<p>${processed}</p>`;
    processed = processed.replace(/<p><\/p>/g, '');

    // Restore fenced code blocks
    processed = processed.replace(/@@CODE_BLOCK_(\d+)@@/g, (match, id) => {
      const block = codeBlocks[parseInt(id, 10)];
      const safeCode = escapeHtml(block.code);
      const rawCodeEncoded = encodeURIComponent(block.code);
      return `
        <div class="kd-chat-code-block">
          <div class="kd-chat-code-header">
            <span><i class="bi bi-code-square"></i> ${block.lang}</span>
            <div class="kd-chat-code-actions">
              <button type="button" class="kd-code-btn btn-copy-code" data-code="${rawCodeEncoded}" title="Copy Code">
                <i class="bi bi-clipboard"></i> Copy
              </button>
              <button type="button" class="kd-code-btn btn-insert-code" data-code="${rawCodeEncoded}" title="Apply to Editor">
                <i class="bi bi-arrow-down-left-square"></i> Insert
              </button>
            </div>
          </div>
          <pre class="kd-chat-code-body"><code>${safeCode}</code></pre>
        </div>
      `;
    });

    return processed;
  }

  function init() {
    const tutorPanel = document.getElementById('kd-ai-tutor-panel');
    const toggleBtn = document.getElementById('btn-toggle-tutor');
    const closeBtn = document.getElementById('btn-close-tutor');
    const chatForm = document.getElementById('ai-tutor-form');
    const chatInput = document.getElementById('ai-chat-input');
    const modeSelect = document.getElementById('ai-learning-mode');
    const clearBtn = document.getElementById('btn-clear-chat');
    const confirmClearBtn = document.getElementById('btn-confirm-clear');
    const retryBtn = document.getElementById('btn-ai-retry');

    if (!tutorPanel) return;

    // Toggle panel
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        tutorState.isOpen = !tutorState.isOpen;
        tutorPanel.classList.toggle('is-open', tutorState.isOpen);
        toggleBtn.classList.toggle('is-active', tutorState.isOpen);
        const grid = document.querySelector('.kd-workspace-grid');
        if (grid) {
          grid.classList.toggle('tutor-collapsed', !tutorState.isOpen);
        }
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        tutorState.isOpen = false;
        tutorPanel.classList.remove('is-open');
        if (toggleBtn) toggleBtn.classList.remove('is-active');
      });
    }

    // Learning Mode change
    if (modeSelect) {
      modeSelect.addEventListener('change', () => {
        tutorState.learningMode = modeSelect.value;
      });
    }

    // Quick prompt pills
    document.querySelectorAll('.kd-quick-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const prompt = pill.dataset.prompt;
        if (prompt) {
          sendTutorAction('/api/ai-tutor/ask/', 'ask_question', prompt, "Consulting AI Tutor...");
        }
      });
    });

    // Chat form submit
    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text || tutorState.isLoading) return;
        chatInput.value = '';
        sendTutorAction('/api/ai-tutor/ask/', 'ask_question', text, "Thinking...");
      });
    }

    // Auto-resize chat input
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          chatForm.dispatchEvent(new Event('submit'));
        }
      });
    }

    // Editor Ribbon Action: Explain Code
    const explainCodeBtn = document.getElementById('btn-explain-code');
    if (explainCodeBtn) {
      explainCodeBtn.addEventListener('click', () => {
        const code = window.KDCompiler ? window.KDCompiler.getCode() : '';
        if (!code.trim()) {
          alert("Please write some code in the editor before requesting an explanation.");
          return;
        }
        sendTutorAction(
          '/api/ai-tutor/explain/',
          'explain_code',
          "Please explain this code line-by-line and clarify its core algorithm and logic.",
          "Analyzing complete source code..."
        );
      });
    }

    // Editor Ribbon Action: Explain Selection
    const explainSelectionBtn = document.getElementById('btn-explain-selection');
    if (explainSelectionBtn) {
      explainSelectionBtn.addEventListener('click', () => {
        const sel = window.KDCompiler ? window.KDCompiler.getSelectedCode() : '';
        if (!sel.trim()) {
          alert("Please highlight/select a snippet of code in the editor first, then click Explain Selection.");
          return;
        }
        sendTutorAction(
          '/api/ai-tutor/explain-selection/',
          'explain_selection',
          "Please explain the highlighted code block and how it connects to the program.",
          "Analyzing selected code snippet..."
        );
      });
    }

    // Editor Ribbon Action: Debug Code
    const debugCodeBtn = document.getElementById('btn-debug-code');
    if (debugCodeBtn) {
      debugCodeBtn.addEventListener('click', () => {
        sendTutorAction(
          '/api/ai-tutor/debug/',
          'debug_code',
          "Please analyze my code and diagnostics, pinpoint the root cause of any bugs, and suggest minimal fixes.",
          "Diagnosing potential bugs..."
        );
      });
    }

    // Editor Ribbon Action: Complexity
    const complexityBtn = document.getElementById('btn-analyze-complexity');
    if (complexityBtn) {
      complexityBtn.addEventListener('click', () => {
        sendTutorAction(
          '/api/ai-tutor/analyze-complexity/',
          'analyze_complexity',
          "Please provide a rigorous time and space complexity analysis (Big-O) for my solution.",
          "Calculating time and space complexity..."
        );
      });
    }

    // Editor Ribbon Action: Improve Code
    const improveBtn = document.getElementById('btn-improve-code');
    if (improveBtn) {
      improveBtn.addEventListener('click', () => {
        sendTutorAction(
          '/api/ai-tutor/improve/',
          'improve_solution',
          "How can I optimize this solution in terms of readability, performance, and best practices?",
          "Formulating optimization suggestions..."
        );
      });
    }

    // Console Action: Explain Stderr Error
    const explainErrorActionBtn = document.getElementById('btn-explain-error-action');
    if (explainErrorActionBtn) {
      explainErrorActionBtn.addEventListener('click', () => {
        sendTutorAction(
          '/api/ai-tutor/explain-error/',
          'explain_error',
          "Why did this compiler or runtime error happen, and what exact steps should I take to fix it?",
          "Investigating compiler diagnostic output..."
        );
      });
    }

    // Console Action: Explain Failed Test
    const explainTestActionBtn = document.getElementById('btn-explain-test-action');
    if (explainTestActionBtn) {
      explainTestActionBtn.addEventListener('click', () => {
        sendTutorAction(
          '/api/ai-tutor/explain-test/',
          'explain_test',
          "My solution failed on this public test case. Can you explain the discrepancy without giving away the full code?",
          "Analyzing failed test evidence..."
        );
      });
    }

    // Clear Conversation Modal
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        const modalEl = document.getElementById('clearHistoryModal');
        if (modalEl && window.bootstrap) {
          const modal = new bootstrap.Modal(modalEl);
          modal.show();
        }
      });
    }

    if (confirmClearBtn) {
      confirmClearBtn.addEventListener('click', async () => {
        if (tutorState.conversationId) {
          try {
            await fetch(`/api/ai-tutor/conversations/${tutorState.conversationId}/clear/`, {
              method: 'POST',
              headers: { 'X-CSRFToken': getCsrfToken() }
            });
          } catch (e) {}
        }
        // Reset message container
        const stream = document.getElementById('ai-chat-messages');
        if (stream) {
          stream.innerHTML = `
            <div class="kd-tutor-welcome-card">
              <div class="kd-welcome-icon"><i class="bi bi-stars"></i></div>
              <h4 class="h6 fw-bold text-light mb-1">Conversation Cleared</h4>
              <p class="text-muted fs-xs mb-0">Ask a new question or choose one of the quick actions to begin.</p>
            </div>
          `;
        }
        tutorState.conversationId = null;
        const modalEl = document.getElementById('clearHistoryModal');
        if (modalEl && window.bootstrap) {
          const modal = bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();
        }
      });
    }

    // Retry Button
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        if (tutorState.lastEndpoint && tutorState.lastPayload) {
          executeRequest(tutorState.lastEndpoint, tutorState.lastPayload, "Retrying...");
        }
      });
    }

    // Event Delegation for Code Copy and Insert
    document.addEventListener('click', (e) => {
      const copyBtn = e.target.closest('.btn-copy-code');
      if (copyBtn) {
        const rawCode = decodeURIComponent(copyBtn.dataset.code || '');
        navigator.clipboard.writeText(rawCode).then(() => {
          copyBtn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
          setTimeout(() => {
            copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
          }, 2000);
        });
        return;
      }

      const insertBtn = e.target.closest('.btn-insert-code');
      if (insertBtn) {
        const rawCode = decodeURIComponent(insertBtn.dataset.code || '');
        if (window.KDCompiler && window.confirm("Apply this suggested code into your editor? (Your current editor content will be updated)")) {
          window.KDCompiler.setCode(rawCode);
          insertBtn.innerHTML = '<i class="bi bi-check2"></i> Applied!';
          setTimeout(() => {
            insertBtn.innerHTML = '<i class="bi bi-arrow-down-left-square"></i> Insert';
          }, 2000);
        }
      }
    });
  }

  function appendUserBubble(question) {
    const stream = document.getElementById('ai-chat-messages');
    if (!stream) return;

    const msg = document.createElement('div');
    msg.className = 'kd-chat-msg user';
    msg.textContent = question;
    stream.appendChild(msg);
    stream.scrollTop = stream.scrollHeight;
  }

  function appendAssistantBubble(responseMarkdown) {
    const stream = document.getElementById('ai-chat-messages');
    if (!stream) return;

    const msg = document.createElement('div');
    msg.className = 'kd-chat-msg assistant';
    msg.innerHTML = renderMarkdownSafe(responseMarkdown);
    stream.appendChild(msg);
    stream.scrollTop = stream.scrollHeight;
  }

  function setLoading(isLoading, text) {
    tutorState.isLoading = isLoading;
    const loader = document.getElementById('ai-loading-indicator');
    const loadingText = document.getElementById('ai-loading-text');
    const statusText = document.getElementById('ai-status-text');
    const errorBanner = document.getElementById('ai-error-banner');
    const sendBtn = document.getElementById('btn-send-doubt');

    if (errorBanner && isLoading) errorBanner.classList.add('d-none');
    if (sendBtn) sendBtn.disabled = isLoading;

    if (loader) {
      if (isLoading) {
        loader.classList.remove('d-none');
        if (loadingText) loadingText.textContent = text || "Thinking...";
        if (statusText) statusText.textContent = "Generating...";
      } else {
        loader.classList.add('d-none');
        if (statusText) statusText.textContent = "Ready to help";
      }
    }
  }

  function showError(msg) {
    const banner = document.getElementById('ai-error-banner');
    const errorText = document.getElementById('ai-error-text');
    if (banner && errorText) {
      errorText.textContent = msg || "An error occurred while connecting to the AI Tutor.";
      banner.classList.remove('d-none');
    }
  }

  async function sendTutorAction(endpoint, featureType, userPrompt, loadingMsg) {
    if (tutorState.isLoading) return;

    // Open tutor drawer if closed
    const tutorPanel = document.getElementById('kd-ai-tutor-panel');
    const toggleBtn = document.getElementById('btn-toggle-tutor');
    if (tutorPanel && !tutorState.isOpen) {
      tutorState.isOpen = true;
      tutorPanel.classList.add('is-open');
      if (toggleBtn) toggleBtn.classList.add('is-active');
      const grid = document.querySelector('.kd-workspace-grid');
      if (grid) grid.classList.remove('tutor-collapsed');
    }

    // Append user query to chat stream
    appendUserBubble(userPrompt);

    // Build context payload
    const compiler = window.KDCompiler || {};
    const payload = {
      feature: featureType,
      code: compiler.getCode ? compiler.getCode() : '',
      language: compiler.getLanguage ? compiler.getLanguage() : 'python',
      selected_code: compiler.getSelectedCode ? compiler.getSelectedCode() : '',
      question: userPrompt,
      problem_id: compiler.getProblemId ? compiler.getProblemId() : null,
      learning_mode: tutorState.learningMode,
      conversation_id: tutorState.conversationId,
      compiler_stderr: compiler.getLastStderr ? compiler.getLastStderr() : '',
      failed_test_case: compiler.getLastFailedTestCase ? compiler.getLastFailedTestCase() : null
    };

    tutorState.lastEndpoint = endpoint;
    tutorState.lastPayload = payload;

    await executeRequest(endpoint, payload, loadingMsg);
  }

  async function executeRequest(endpoint, payload, loadingMsg) {
    setLoading(true, loadingMsg);

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
      });

      const res = await response.json();

      if (res.success) {
        tutorState.conversationId = res.conversation_id || tutorState.conversationId;
        appendAssistantBubble(res.response);
      } else {
        const errMsg = res.error ? res.error.message : "Failed to receive AI Tutor guidance.";
        showError(errMsg);
      }
    } catch (err) {
      console.error("AI Tutor request error:", err);
      showError("Network error: Could not reach the AI Tutor service.");
    } finally {
      setLoading(false);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
