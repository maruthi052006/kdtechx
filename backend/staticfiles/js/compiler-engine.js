/**
 * KDTechX Online Compiler Engine
 * Manages editor state, line numbers, execution calls, and test case evaluation.
 */
(function () {
  'use strict';

  const state = {
    language: 'python',
    code: '',
    isRunning: false,
    problemId: null,
    lastStderr: '',
    lastFailedTestCase: null
  };

  // Language file extensions and default boilerplates
  const templates = {
    python: {
      filename: 'solution.py',
      code: "# Write Python 3 code here\ndef main():\n    print(\"Hello from Python!\")\n\nif __name__ == '__main__':\n    main()\n"
    },
    javascript: {
      filename: 'solution.js',
      code: "// Write Node.js JavaScript code here\nconsole.log(\"Hello from JavaScript!\");\n"
    },
    cpp: {
      filename: 'main.cpp',
      code: "#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << \"Hello from C++!\" << endl;\n    return 0;\n}\n"
    },
    c: {
      filename: 'main.c',
      code: "#include <stdio.h>\n\nint main() {\n    printf(\"Hello from C!\\n\");\n    return 0;\n}\n"
    },
    java: {
      filename: 'Main.java',
      code: "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello from Java!\");\n    }\n}\n"
    }
  };

  function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  function init() {
    const editor = document.getElementById('kd-code-editor');
    const lineNumbers = document.getElementById('kd-line-numbers');
    const langSelect = document.getElementById('compiler-lang-select');
    const runBtn = document.getElementById('btn-run-code');
    const submitBtn = document.getElementById('btn-submit-solution');
    const filenameLabel = document.getElementById('editor-filename');

    if (!editor) return;

    state.problemId = editor.dataset.problemId ? parseInt(editor.dataset.problemId, 10) : null;
    state.language = langSelect ? langSelect.value : 'python';

    // Synchronize line numbers
    function updateLineNumbers() {
      const lines = editor.value.split('\n').length;
      let html = '';
      for (let i = 1; i <= lines; i++) {
        html += `<span>${i}</span>`;
      }
      lineNumbers.innerHTML = html;
    }

    editor.addEventListener('input', updateLineNumbers);
    editor.addEventListener('scroll', () => {
      lineNumbers.scrollTop = editor.scrollTop;
    });

    // Support Tab key indentation
    editor.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
        editor.selectionStart = editor.selectionEnd = start + 4;
        updateLineNumbers();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        runCode();
      }
    });

    updateLineNumbers();

    // Language switcher
    if (langSelect) {
      langSelect.addEventListener('change', () => {
        const newLang = langSelect.value;
        state.language = newLang;
        if (filenameLabel && templates[newLang]) {
          filenameLabel.textContent = templates[newLang].filename;
        }
        // Only swap template if editor is empty or matches previous default
        if (!editor.value.trim() && templates[newLang]) {
          editor.value = templates[newLang].code;
          updateLineNumbers();
        }
      });
    }

    // Run Code Button
    if (runBtn) {
      runBtn.addEventListener('click', runCode);
    }

    // Submit Solution Button
    if (submitBtn) {
      submitBtn.addEventListener('click', submitSolution);
    }

    // Console Tabs
    document.querySelectorAll('[data-console-tab]').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.consoleTab;
        document.querySelectorAll('[data-console-tab]').forEach(b => b.classList.remove('is-active'));
        document.querySelectorAll('.kd-console-tab-pane').forEach(p => p.classList.remove('is-active'));
        btn.classList.add('is-active');
        const target = document.getElementById(`pane-console-${tab}`);
        if (target) target.classList.add('is-active');
      });
    });

    // Problem Panel Tabs
    document.querySelectorAll('[data-problem-tab]').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.problemTab;
        document.querySelectorAll('[data-problem-tab]').forEach(b => b.classList.remove('is-active'));
        document.querySelectorAll('#kd-problem-panel .kd-tab-content').forEach(c => c.classList.remove('is-active'));
        btn.classList.add('is-active');
        const target = document.getElementById(`tab-problem-${tab}`);
        if (target) target.classList.add('is-active');
      });
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
  }

  async function runCode() {
    const editor = document.getElementById('kd-code-editor');
    const customInput = document.getElementById('kd-custom-input');
    const runBtn = document.getElementById('btn-run-code');
    const stdoutPre = document.getElementById('console-stdout');
    const stderrPre = document.getElementById('console-stderr');
    const statusBadge = document.getElementById('exec-status-badge');
    const timeBadge = document.getElementById('exec-time-badge');
    const errorDot = document.getElementById('console-error-dot');
    const explainErrorCta = document.getElementById('error-explain-cta');

    if (!editor || state.isRunning) return;

    const code = editor.value;
    if (!code.trim()) {
      alert("Please write some code before running.");
      return;
    }

    state.isRunning = true;
    if (runBtn) {
      runBtn.disabled = true;
      runBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> <span>Running...</span>';
    }
    if (statusBadge) statusBadge.textContent = "Executing in sandbox...";

    try {
      const response = await fetch('/api/compiler/run/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          language: state.language,
          code: code,
          input: customInput ? customInput.value : ''
        })
      });

      const res = await response.json();

      if (res.success) {
        if (stdoutPre) stdoutPre.textContent = res.stdout || "(Program produced no standard output)";
        if (stderrPre) stderrPre.textContent = res.stderr || "No errors reported.";
        state.lastStderr = res.stderr || '';

        if (statusBadge) {
          if (res.timed_out) {
            statusBadge.innerHTML = '<span class="text-danger fw-bold">Time Limit Exceeded</span>';
          } else if (res.exit_code === 0) {
            statusBadge.innerHTML = '<span class="text-success fw-bold">Success (Exit 0)</span>';
          } else {
            statusBadge.innerHTML = `<span class="text-danger fw-bold">Failed (Exit ${res.exit_code})</span>`;
          }
        }
        if (timeBadge) timeBadge.textContent = `${res.execution_time_ms}ms`;

        // Switch to Errors tab if an error occurred
        if (res.stderr || res.exit_code !== 0 || res.timed_out) {
          if (errorDot) errorDot.classList.remove('d-none');
          if (explainErrorCta) explainErrorCta.classList.remove('d-none');
          const errTabBtn = document.querySelector('[data-console-tab="errors"]');
          if (errTabBtn) errTabBtn.click();
        } else {
          if (errorDot) errorDot.classList.add('d-none');
          if (explainErrorCta) explainErrorCta.classList.add('d-none');
          const outTabBtn = document.querySelector('[data-console-tab="output"]');
          if (outTabBtn) outTabBtn.click();
        }
      } else {
        alert(res.error ? res.error.message : "Execution failed.");
      }
    } catch (err) {
      console.error("Execution error:", err);
      if (stderrPre) stderrPre.textContent = "Network error while connecting to execution engine.";
    } finally {
      state.isRunning = false;
      if (runBtn) {
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="bi bi-play-fill"></i> <span>Run Code</span>';
      }
    }
  }

  async function submitSolution() {
    const editor = document.getElementById('kd-code-editor');
    const submitBtn = document.getElementById('btn-submit-solution');
    const testCasesPane = document.getElementById('console-testcases-results');
    const testBadge = document.getElementById('console-test-badge');
    const explainTestCta = document.getElementById('test-explain-cta');

    if (!editor || !state.problemId || state.isRunning) return;

    state.isRunning = true;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> <span>Evaluating...</span>';
    }

    try {
      const response = await fetch('/api/compiler/submit/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          problem_id: state.problemId,
          language: state.language,
          code: editor.value
        })
      });

      const res = await response.json();

      if (res.success) {
        // Switch to testcases tab
        const testTabBtn = document.querySelector('[data-console-tab="testcases"]');
        if (testTabBtn) testTabBtn.click();

        // Render test verdicts
        let html = `
          <div class="d-flex align-items-center justify-content-between p-2 mb-3 rounded" style="background: var(--kd-surface-2); border: 1px solid var(--kd-border);">
            <div>
              <span class="fw-bold text-uppercase ${res.status === 'accepted' ? 'text-success' : 'text-danger'}">${res.status.replace('_', ' ')}</span>
              <span class="text-muted fs-xs ms-2">• Passed ${res.passed_count} of ${res.total_count} test cases</span>
            </div>
            <span class="text-muted fs-xs">${res.total_time_ms}ms total</span>
          </div>
          <div class="d-flex flex-column gap-2">
        `;

        state.lastFailedTestCase = null;

        res.test_cases.forEach((tc) => {
          const pass = tc.passed;
          if (!pass && !state.lastFailedTestCase && !tc.is_hidden) {
            state.lastFailedTestCase = tc;
          }

          html += `
            <div class="p-2 px-3 rounded border d-flex flex-column gap-1" style="background: #090d16; border-color: ${pass ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'} !important;">
              <div class="d-flex align-items-center justify-content-between">
                <span class="fw-bold fs-xs ${pass ? 'text-success' : 'text-danger'}">
                  <i class="bi ${pass ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}"></i>
                  Test Case #${tc.case_index} ${tc.is_hidden ? '(Hidden)' : ''}
                </span>
                <span class="text-muted fs-xs">${tc.execution_time_ms}ms</span>
              </div>
          `;

          if (!tc.is_hidden) {
            html += `
              <div class="fs-xs text-muted">Input: <code>${tc.input || ''}</code></div>
              <div class="fs-xs text-muted">Expected: <code>${tc.expected_output || ''}</code></div>
              <div class="fs-xs text-muted">Output: <code class="${pass ? 'text-success' : 'text-danger'}">${tc.actual_output || '(Empty)'}</code></div>
            `;
          }

          if (tc.error) {
            html += `<div class="fs-xs text-danger mt-1">${tc.error}</div>`;
          }

          html += `</div>`;
        });

        html += `</div>`;
        if (testCasesPane) testCasesPane.innerHTML = html;

        if (res.passed_count < res.total_count) {
          if (explainTestCta) explainTestCta.classList.remove('d-none');
          if (testBadge) {
            testBadge.textContent = `${res.passed_count}/${res.total_count}`;
            testBadge.className = 'kd-pill-badge bg-danger ms-1';
          }
        } else {
          if (explainTestCta) explainTestCta.classList.add('d-none');
          if (testBadge) {
            testBadge.textContent = `${res.passed_count}/${res.total_count}`;
            testBadge.className = 'kd-pill-badge bg-success ms-1';
          }
        }
      } else {
        alert(res.error ? res.error.message : "Submission failed.");
      }
    } catch (err) {
      console.error("Submission error:", err);
      alert("Failed to submit solution due to network error.");
    } finally {
      state.isRunning = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-send-check"></i> <span>Submit Solution</span>';
      }
    }
  }

  // Global accessors for AI Tutor integration
  window.KDCompiler = {
    getCode: () => {
      const el = document.getElementById('kd-code-editor');
      return el ? el.value : '';
    },
    setCode: (newCode) => {
      const el = document.getElementById('kd-code-editor');
      if (el) {
        el.value = newCode;
        const event = new Event('input');
        el.dispatchEvent(event);
      }
    },
    getSelectedCode: () => {
      const el = document.getElementById('kd-code-editor');
      if (!el) return '';
      return el.value.substring(el.selectionStart, el.selectionEnd);
    },
    getLanguage: () => state.language,
    getProblemId: () => state.problemId,
    getLastStderr: () => state.lastStderr,
    getLastFailedTestCase: () => state.lastFailedTestCase
  };

  document.addEventListener('DOMContentLoaded', init);
})();
