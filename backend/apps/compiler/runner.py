import os
import sys
import time
import shutil
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from django.conf import settings


MAX_OUTPUT_BYTES = getattr(settings, 'COMPILER_MAX_OUTPUT_BYTES', 65536)
DEFAULT_TIMEOUT = getattr(settings, 'COMPILER_EXECUTION_TIMEOUT', 5)


class CodeExecutionResult:
    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
        execution_time_ms: int = 0,
        timed_out: bool = False,
        compile_error: bool = False
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time_ms = execution_time_ms
        self.timed_out = timed_out
        self.compile_error = compile_error

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stdout': self.stdout[:MAX_OUTPUT_BYTES],
            'stderr': self.stderr[:MAX_OUTPUT_BYTES],
            'exit_code': self.exit_code,
            'execution_time_ms': self.execution_time_ms,
            'timed_out': self.timed_out,
            'compile_error': self.compile_error,
            'success': (self.exit_code == 0 and not self.timed_out and not self.compile_error)
        }


def execute_code(
    language: str,
    source_code: str,
    stdin_input: str = "",
    timeout_seconds: Optional[float] = None
) -> CodeExecutionResult:
    """
    Executes source code in an isolated subprocess with strictly bounded time,
    input, and output limits.
    """
    timeout = timeout_seconds or DEFAULT_TIMEOUT
    lang = (language or 'python').lower().strip()
    
    # Create isolated ephemeral workspace
    with tempfile.TemporaryDirectory(prefix="kd_sandbox_") as temp_dir:
        start_time = time.perf_counter()
        
        try:
            if lang in ('python', 'python3', 'py'):
                return _run_python(temp_dir, source_code, stdin_input, timeout, start_time)
            elif lang in ('javascript', 'node', 'js'):
                return _run_javascript(temp_dir, source_code, stdin_input, timeout, start_time)
            elif lang in ('cpp', 'c++', 'cxx'):
                return _run_cpp(temp_dir, source_code, stdin_input, timeout, start_time)
            elif lang in ('c',):
                return _run_c(temp_dir, source_code, stdin_input, timeout, start_time)
            elif lang in ('java',):
                return _run_java(temp_dir, source_code, stdin_input, timeout, start_time)
            else:
                return CodeExecutionResult(
                    stderr=f"Unsupported language: '{language}'. Supported: python, javascript, cpp, c, java.",
                    exit_code=1,
                    compile_error=True
                )
        except Exception as ex:
            elapsed = int((time.perf_counter() - start_time) * 1000)
            return CodeExecutionResult(
                stderr=f"Runtime engine exception: {str(ex)}",
                exit_code=1,
                execution_time_ms=elapsed
            )


def _run_python(temp_dir: str, code: str, stdin_data: str, timeout: float, start_time: float) -> CodeExecutionResult:
    script_path = os.path.join(temp_dir, "solution.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    # Execute with current python executable
    cmd = [sys.executable, "-u", script_path]
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=temp_dir
        )
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            execution_time_ms=elapsed
        )
    except subprocess.TimeoutExpired as te:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        stdout = te.stdout.decode('utf-8', errors='replace') if isinstance(te.stdout, bytes) else (te.stdout or '')
        return CodeExecutionResult(
            stdout=stdout,
            stderr=f"Execution timed out after {timeout} seconds.",
            exit_code=-1,
            execution_time_ms=elapsed,
            timed_out=True
        )


def _run_javascript(temp_dir: str, code: str, stdin_data: str, timeout: float, start_time: float) -> CodeExecutionResult:
    node_bin = shutil.which("node") or shutil.which("nodejs")
    if not node_bin:
        # Fallback if Node.js is not installed on host: provide informative message
        return CodeExecutionResult(
            stderr="Node.js engine is not configured in this host environment. Please choose Python 3 or contact admin.",
            exit_code=1,
            compile_error=True
        )

    script_path = os.path.join(temp_dir, "solution.js")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    cmd = [node_bin, script_path]
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=temp_dir
        )
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            execution_time_ms=elapsed
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stderr=f"Execution timed out after {timeout} seconds.",
            exit_code=-1,
            execution_time_ms=elapsed,
            timed_out=True
        )


def _run_cpp(temp_dir: str, code: str, stdin_data: str, timeout: float, start_time: float) -> CodeExecutionResult:
    gpp_bin = shutil.which("g++") or shutil.which("clang++")
    if not gpp_bin:
        return CodeExecutionResult(
            stderr="C++ compiler (g++/clang++) is not configured in this host environment. Please choose Python 3 or contact admin.",
            exit_code=1,
            compile_error=True
        )

    src_file = os.path.join(temp_dir, "main.cpp")
    bin_file = os.path.join(temp_dir, "main.exe" if os.name == 'nt' else "main")
    with open(src_file, "w", encoding="utf-8") as f:
        f.write(code)

    # Compile
    compile_proc = subprocess.run(
        [gpp_bin, "-O2", "-std=c++17", src_file, "-o", bin_file],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=temp_dir
    )
    if compile_proc.returncode != 0:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stderr=f"Compilation Error:\n{compile_proc.stderr}",
            exit_code=compile_proc.returncode,
            execution_time_ms=elapsed,
            compile_error=True
        )

    # Run compiled binary
    try:
        proc = subprocess.run(
            [bin_file],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=temp_dir
        )
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            execution_time_ms=elapsed
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stderr=f"Execution timed out after {timeout} seconds.",
            exit_code=-1,
            execution_time_ms=elapsed,
            timed_out=True
        )


def _run_c(temp_dir: str, code: str, stdin_data: str, timeout: float, start_time: float) -> CodeExecutionResult:
    gcc_bin = shutil.which("gcc") or shutil.which("clang")
    if not gcc_bin:
        return CodeExecutionResult(
            stderr="C compiler (gcc/clang) is not configured in this host environment. Please choose Python 3.",
            exit_code=1,
            compile_error=True
        )

    src_file = os.path.join(temp_dir, "main.c")
    bin_file = os.path.join(temp_dir, "main.exe" if os.name == 'nt' else "main")
    with open(src_file, "w", encoding="utf-8") as f:
        f.write(code)

    compile_proc = subprocess.run(
        [gcc_bin, "-O2", src_file, "-o", bin_file],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=temp_dir
    )
    if compile_proc.returncode != 0:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stderr=f"Compilation Error:\n{compile_proc.stderr}",
            exit_code=compile_proc.returncode,
            execution_time_ms=elapsed,
            compile_error=True
        )

    try:
        proc = subprocess.run(
            [bin_file],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=temp_dir
        )
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            execution_time_ms=elapsed
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stderr=f"Execution timed out after {timeout} seconds.",
            exit_code=-1,
            execution_time_ms=elapsed,
            timed_out=True
        )


def _run_java(temp_dir: str, code: str, stdin_data: str, timeout: float, start_time: float) -> CodeExecutionResult:
    javac_bin = shutil.which("javac")
    java_bin = shutil.which("java")
    if not javac_bin or not java_bin:
        return CodeExecutionResult(
            stderr="Java compiler/runtime (javac/java) is not configured in this host environment.",
            exit_code=1,
            compile_error=True
        )

    src_file = os.path.join(temp_dir, "Main.java")
    with open(src_file, "w", encoding="utf-8") as f:
        f.write(code)

    compile_proc = subprocess.run(
        [javac_bin, src_file],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=temp_dir
    )
    if compile_proc.returncode != 0:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stderr=f"Java Compilation Error:\n{compile_proc.stderr}",
            exit_code=compile_proc.returncode,
            execution_time_ms=elapsed,
            compile_error=True
        )

    try:
        proc = subprocess.run(
            [java_bin, "Main"],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=temp_dir
        )
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            execution_time_ms=elapsed
        )
    except subprocess.TimeoutExpired:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return CodeExecutionResult(
            stderr=f"Execution timed out after {timeout} seconds.",
            exit_code=-1,
            execution_time_ms=elapsed,
            timed_out=True
        )


def evaluate_test_cases(
    language: str,
    source_code: str,
    test_cases: List[Dict[str, Any]],
    timeout_per_case: float = 3.0
) -> Dict[str, Any]:
    """
    Evaluates source code against an ordered set of test cases.
    Returns summary statistics, individual case outcomes, and execution metrics.
    """
    results = []
    passed_count = 0
    total_time_ms = 0
    overall_status = "accepted"

    for idx, tc in enumerate(test_cases, start=1):
        inp = str(tc.get('input', ''))
        expected = str(tc.get('expected_output', '')).strip()
        explanation = tc.get('explanation', '')

        res = execute_code(language, source_code, stdin_input=inp, timeout_seconds=timeout_per_case)
        actual = res.stdout.strip()
        total_time_ms += res.execution_time_ms

        is_passed = False
        error_message = ""

        if res.compile_error:
            is_passed = False
            error_message = res.stderr
            overall_status = "compile_error"
        elif res.timed_out:
            is_passed = False
            error_message = "Time Limit Exceeded"
            overall_status = "time_limit_exceeded"
        elif res.exit_code != 0:
            is_passed = False
            error_message = res.stderr or f"Runtime error with exit code {res.exit_code}"
            overall_status = "runtime_error"
        else:
            # Normalize line endings and trailing whitespace
            norm_actual = "\n".join(line.rstrip() for line in actual.splitlines())
            norm_expected = "\n".join(line.rstrip() for line in expected.splitlines())
            if norm_actual == norm_expected:
                is_passed = True
                passed_count += 1
            else:
                is_passed = False
                error_message = "Output did not match expected result."
                if overall_status == "accepted":
                    overall_status = "wrong_answer"

        results.append({
            'case_index': idx,
            'passed': is_passed,
            'input': inp,
            'expected_output': expected,
            'actual_output': actual if not res.compile_error and not res.timed_out else "",
            'error': error_message,
            'execution_time_ms': res.execution_time_ms,
            'explanation': explanation
        })

        # Break early if compilation failed on case 1
        if res.compile_error:
            break

    if passed_count == len(test_cases) and len(test_cases) > 0:
        overall_status = "accepted"

    return {
        'status': overall_status,
        'passed_count': passed_count,
        'total_count': len(test_cases),
        'total_time_ms': total_time_ms,
        'test_cases': results
    }
