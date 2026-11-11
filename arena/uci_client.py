"""
arena/uci_client.py

Controls one engine subprocess (arena/uci_server.py) over the UCI dialect.

Reading uses a background thread + queue instead of select(), because select()
does not work on pipes on Windows. Every wait has a deadline, so a hung engine
becomes an EngineTimeout rather than hanging the arena.
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import EngineConfig

SERVER_PATH = Path(__file__).with_name("uci_server.py")
STARTUP_TIMEOUT = 30.0
SYNC_TIMEOUT = 30.0
MATE_CP = 32000   # centipawn value used for mate scores in statistics / adjudication


class EngineError(RuntimeError):
    """Base class for problems with an engine process."""


class EngineStartupError(EngineError):
    """The engine could not be started or did not complete the UCI handshake."""


class EngineTimeout(EngineError):
    """The engine did not answer in time."""


class EngineCrash(EngineError):
    """The engine process died or closed its output."""


@dataclass
class SearchResult:
    bestmove: str = ""
    depth: int = 0
    score_cp: Optional[int] = None   # from the engine's own point of view (side to move)
    mate: Optional[int] = None       # moves to mate, negative if the engine is being mated
    nodes: int = 0
    engine_ms: int = 0               # time the engine reported
    wall_s: float = 0.0              # time the arena measured, `go` sent -> `bestmove` received


# Every live engine, so Ctrl+C can kill them all.
_LIVE: set["UciEngine"] = set()
_LIVE_LOCK = threading.Lock()


def kill_all_engines() -> None:
    with _LIVE_LOCK:
        engines = list(_LIVE)
    for engine in engines:
        engine.kill()


class UciEngine:
    def __init__(self, cfg: EngineConfig, repo_root: Path, seed: int = 0):
        self.cfg = cfg
        self.root = Path(cfg.root).expanduser().resolve() if cfg.root else Path(repo_root).resolve()
        self.seed = seed
        self.name = cfg.label
        self.caps: dict[str, str] = {}
        self.proc: Optional[subprocess.Popen] = None
        self._lines: "queue.Queue[Optional[str]]" = queue.Queue()
        self._stderr_tail: deque[str] = deque(maxlen=40)
        self._eof = False

    # ── lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        if not self.root.is_dir():
            raise EngineStartupError(f"{self.name}: root directory {self.root} does not exist")
        cmd = [sys.executable, "-u", str(SERVER_PATH), "--engine", self.cfg.package, "--root", str(self.root)]
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        try:
            self.proc = subprocess.Popen(
                cmd, cwd=str(self.root), env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", bufsize=1,
            )
        except OSError as e:
            raise EngineStartupError(f"{self.name}: could not launch {cmd[0]}: {e}") from e

        with _LIVE_LOCK:
            _LIVE.add(self)
        threading.Thread(target=self._pump_stdout, daemon=True).start()
        threading.Thread(target=self._pump_stderr, daemon=True).start()

        try:
            deadline = time.monotonic() + STARTUP_TIMEOUT
            self._send("uci")
            while True:
                line = self._next_line(deadline)
                if line.startswith("info string caps"):
                    for token in line.split()[3:]:
                        key, _, value = token.partition("=")
                        self.caps[key] = value
                elif line.strip() == "uciok":
                    break
            self._send(f"setoption name Vary value {'true' if self.cfg.vary else 'false'}")
            self._send(f"setoption name Seed value {self.seed}")
            self.sync()
        except EngineError as e:
            self.kill()
            raise EngineStartupError(f"{self.name}: failed to start: {e}") from e

    def close(self) -> None:
        """Polite shutdown, then force."""
        proc = self.proc
        if proc is None:
            return
        try:
            if proc.poll() is None:
                self._send("quit")
                proc.wait(timeout=2)
        except Exception:
            pass
        self.kill()

    def kill(self) -> None:
        proc = self.proc
        with _LIVE_LOCK:
            _LIVE.discard(self)
        if proc is None:
            return
        try:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                if stream:
                    stream.close()
            except Exception:
                pass

    def __enter__(self) -> "UciEngine":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ── protocol ──────────────────────────────────────────────────────────

    def new_game(self) -> None:
        self._send("ucinewgame")
        self.sync()

    def sync(self, timeout: float = SYNC_TIMEOUT) -> None:
        """isready / readyok round trip: everything sent so far has been processed."""
        self._send("isready")
        deadline = time.monotonic() + timeout
        while self._next_line(deadline).strip() != "readyok":
            pass

    def set_position(self, fen: str, moves: list[str]) -> None:
        cmd = f"position fen {fen}"
        if moves:
            cmd += " moves " + " ".join(moves)
        self._send(cmd)
        self.sync()   # so the time spent replaying moves is not charged to the engine's clock

    def go(self, args: str, timeout: float) -> SearchResult:
        """
        Send `go <args>` and wait for `bestmove`.

        Raises EngineTimeout if no answer arrives within `timeout` seconds and
        EngineCrash if the process dies.
        """
        result = SearchResult()
        started = time.perf_counter()
        self._send(f"go {args}")
        deadline = time.monotonic() + timeout
        while True:
            line = self._next_line(deadline)
            if line.startswith("info "):
                self._parse_info(line, result)
            elif line.startswith("bestmove"):
                parts = line.split()
                result.bestmove = parts[1] if len(parts) > 1 else ""
                result.wall_s = time.perf_counter() - started
                return result

    # ── internals ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_info(line: str, result: SearchResult) -> None:
        tokens = line.split()
        i = 1
        while i < len(tokens):
            t = tokens[i]
            try:
                if t == "string":
                    return
                if t == "depth":
                    result.depth = int(tokens[i + 1]); i += 2
                elif t == "nodes":
                    result.nodes = int(tokens[i + 1]); i += 2
                elif t == "time":
                    result.engine_ms = int(tokens[i + 1]); i += 2
                elif t == "score":
                    kind, value = tokens[i + 1], int(tokens[i + 2])
                    if kind == "cp":
                        result.score_cp, result.mate = value, None
                    elif kind == "mate":
                        result.mate = value
                        result.score_cp = MATE_CP if value > 0 else -MATE_CP
                    i += 3
                else:
                    i += 1
            except (IndexError, ValueError):
                return

    def _send(self, line: str) -> None:
        try:
            assert self.proc is not None and self.proc.stdin is not None
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()
        except (OSError, ValueError, AssertionError) as e:
            raise EngineCrash(f"{self.name}: could not write {line.split()[0]!r}: {e}{self.crash_info()}") from e

    def _next_line(self, deadline: float) -> str:
        if self._eof:
            raise EngineCrash(f"{self.name}: engine process exited{self.crash_info()}")
        remaining = deadline - time.monotonic()
        try:
            line = self._lines.get(timeout=max(remaining, 0.0)) if remaining > 0 else self._lines.get_nowait()
        except queue.Empty:
            raise EngineTimeout(f"{self.name}: no response in time") from None
        if line is None:
            self._eof = True
            raise EngineCrash(f"{self.name}: engine process exited{self.crash_info()}")
        return line

    def _pump_stdout(self) -> None:
        try:
            for line in self.proc.stdout:           # type: ignore[union-attr]
                self._lines.put(line.rstrip("\r\n"))
        except (OSError, ValueError):
            pass
        finally:
            self._lines.put(None)

    def _pump_stderr(self) -> None:
        try:
            for line in self.proc.stderr:           # type: ignore[union-attr]
                self._stderr_tail.append(line.rstrip("\r\n"))
        except (OSError, ValueError):
            pass

    def crash_info(self) -> str:
        code = self.proc.poll() if self.proc else None
        tail = "\n".join(list(self._stderr_tail)[-8:])
        text = f" (exit code {code})" if code is not None else ""
        return f"{text}\n--- engine stderr ---\n{tail}" if tail else text
