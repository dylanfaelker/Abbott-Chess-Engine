"""
arena/config.py

Configuration objects for an engine-vs-engine match, plus the parsing helpers
used by the CLI and by JSON config files.

Every duration in this module is in SECONDS (floats). The UCI layer converts to
milliseconds at the protocol boundary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields, asdict
from pathlib import Path
from typing import Any, Optional


class ConfigError(ValueError):
    """Raised for an invalid match configuration."""


# ── Engines ───────────────────────────────────────────────────────────────────

@dataclass
class EngineConfig:
    """
    One competitor.

    Limits (all optional, combine as you like):
        depth      Max search depth. With no time limit the engine always searches
                   exactly this deep; with a time limit it is a ceiling.
        movetime   Fixed seconds per move (UCI `go movetime`).
        base       Seconds on the clock for the whole game (sudden death), with
                   `increment` seconds added after every move. The engine decides
                   how to spend its clock; the arena enforces flag fall.
    `movetime` and `base` are mutually exclusive.
    """
    package: str                       # importable package at the repo root, e.g. "engine"
    name: str = ""                     # label used in reports (defaults to the package)
    root: Optional[str] = None         # alternative repo root, e.g. a git worktree of an old commit
    depth: Optional[int] = None
    movetime: Optional[float] = None
    base: Optional[float] = None
    increment: float = 0.0
    vary: bool = True                  # engine's random evaluation noise (isVary)

    @property
    def label(self) -> str:
        return self.name or self.package

    def limits_text(self) -> str:
        parts = []
        if self.depth is not None:
            parts.append(f"depth {self.depth}")
        if self.movetime is not None:
            parts.append(f"{self.movetime:g}s/move")
        if self.base is not None:
            parts.append(f"{self.base:g}s+{self.increment:g}s clock")
        return ", ".join(parts) or "no limits"


_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}


def _to_bool(text: str) -> bool:
    t = text.strip().lower()
    if t in _BOOL_TRUE:
        return True
    if t in _BOOL_FALSE:
        return False
    raise ConfigError(f"Expected true/false, got {text!r}")


def parse_time_control(text: str) -> tuple[float, float]:
    """'60+0.5' -> (60.0, 0.5); '60' -> (60.0, 0.0). Seconds."""
    base, _, inc = text.partition("+")
    try:
        return float(base), float(inc) if inc else 0.0
    except ValueError:
        raise ConfigError(f"Bad time control {text!r}; expected BASE[+INC] in seconds, e.g. 60+0.5") from None


def parse_engine_spec(spec: str) -> EngineConfig:
    """
    Parse the CLI form  PACKAGE[:key=value,key=value,...]

        engine
        engine:name=v2.3,depth=4
        engine_v2_2:name=v2.2,movetime=0.5,vary=false
        engine:name=old,root=../abbott-v2.2-worktree,tc=60+0.5

    Keys: name, root, depth, movetime, base, inc (increment), tc (BASE+INC), vary.
    Only the first ':' separates the package from the options, so Windows paths
    such as root=C:\\code\\abbott are fine.
    """
    package, _, rest = spec.partition(":")
    package = package.strip()
    if not package:
        raise ConfigError(f"Engine spec {spec!r} has no package name")
    kwargs: dict[str, Any] = {}
    for item in filter(None, (x.strip() for x in rest.split(","))):
        key, sep, value = item.partition("=")
        key, value = key.strip().lower(), value.strip()
        if not sep:
            raise ConfigError(f"Engine option {item!r} in {spec!r} should look like key=value")
        try:
            if key == "name":
                kwargs["name"] = value
            elif key == "root":
                kwargs["root"] = value
            elif key == "depth":
                kwargs["depth"] = int(value)
            elif key == "movetime":
                kwargs["movetime"] = float(value)
            elif key == "base":
                kwargs["base"] = float(value)
            elif key in ("inc", "increment"):
                kwargs["increment"] = float(value)
            elif key == "tc":
                kwargs["base"], kwargs["increment"] = parse_time_control(value)
            elif key == "vary":
                kwargs["vary"] = _to_bool(value)
            else:
                raise ConfigError(f"Unknown engine option {key!r} in {spec!r}")
        except ValueError:
            raise ConfigError(f"Bad value {value!r} for {key!r} in {spec!r}") from None
    return EngineConfig(package=package, **kwargs)


# ── Openings ──────────────────────────────────────────────────────────────────

@dataclass
class OpeningConfig:
    """
    Where start positions come from.

        start    every game starts from the normal starting position
        random   random legal moves from the start position, kept only if the
                 material is roughly balanced (see arena/openings.py)
        file     pick at random from a FEN/EPD file (one position per line)
    """
    source: str = "random"
    file: Optional[str] = None
    plies: int = 6                 # random: number of random half-moves played
    max_imbalance: int = 100       # random: max |material difference| in centipawns

    @classmethod
    def from_string(cls, text: str) -> "OpeningConfig":
        t = text.strip()
        if t.lower() in ("start", "none"):
            return cls(source="start")
        if t.lower() == "random":
            return cls(source="random")
        return cls(source="file", file=t)


# ── Match ─────────────────────────────────────────────────────────────────────

@dataclass
class MatchConfig:
    engines: list[EngineConfig] = field(default_factory=list)
    name: str = "match"
    games: int = 20
    concurrency: int = 1
    seed: Optional[int] = None             # None -> a random seed is chosen and recorded

    # Defaults applied to any engine that does not set its own limit.
    depth: Optional[int] = None
    movetime: Optional[float] = None
    base: Optional[float] = None
    increment: float = 0.0

    openings: OpeningConfig = field(default_factory=OpeningConfig)
    pair_openings: bool = True             # each opening is played twice, colours swapped

    max_plies: int = 300                   # game is drawn when this many half-moves have been played
    move_timeout: float = 600.0            # kill an engine that takes longer than this per move
                                           # (only used when it has no movetime / clock)
    resign_cp: Optional[int] = None        # adjudicate a loss if an engine's own score <= -resign_cp ...
    resign_moves: int = 4                  # ... for this many consecutive moves of its own
    draw_cp: Optional[int] = None          # adjudicate a draw if both scores stay within +-draw_cp ...
    draw_moves: int = 8                    # ... for this many consecutive moves each ...
    draw_after: int = 80                   # ... but only once this many plies have been played

    output_dir: str = "arena/results"

    # -- construction -------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MatchConfig":
        data = dict(data)
        if "tc" in data:  # convenience: "tc": "60+0.5" means base=60, increment=0.5
            data["base"], data["increment"] = parse_time_control(str(data.pop("tc")))
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ConfigError(f"Unknown config key(s): {', '.join(sorted(unknown))}. Known keys: {', '.join(sorted(known))}")

        engines = []
        for e in data.pop("engines", []):
            if isinstance(e, str):
                engines.append(parse_engine_spec(e))
            else:
                ek = {f.name for f in fields(EngineConfig)}
                bad = set(e) - ek
                if bad:
                    raise ConfigError(f"Unknown engine key(s): {', '.join(sorted(bad))}. Known keys: {', '.join(sorted(ek))}")
                engines.append(EngineConfig(**e))

        opening = data.pop("openings", {})
        if isinstance(opening, str):
            opening = OpeningConfig.from_string(opening)
        elif isinstance(opening, dict):
            ok = {f.name for f in fields(OpeningConfig)}
            bad = set(opening) - ok
            if bad:
                raise ConfigError(f"Unknown openings key(s): {', '.join(sorted(bad))}. Known keys: {', '.join(sorted(ok))}")
            opening = OpeningConfig(**opening)

        return cls(engines=engines, openings=opening, **data)

    @classmethod
    def from_json(cls, path: str | Path) -> "MatchConfig":
        try:
            return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            raise ConfigError(f"{path}: invalid JSON ({e})") from None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    # -- derived ------------------------------------------------------------

    def resolved_engines(self) -> list[EngineConfig]:
        """Engines with the match-level default limits filled in."""
        out = []
        for e in self.engines:
            r = EngineConfig(**asdict(e))
            if r.depth is None:
                r.depth = self.depth
            if r.movetime is None and r.base is None:
                r.movetime, r.base, r.increment = self.movetime, self.base, self.increment
            out.append(r)
        return out

    def validate(self) -> None:
        if len(self.engines) != 2:
            raise ConfigError(f"A match needs exactly 2 engines, got {len(self.engines)}")
        if self.games < 1:
            raise ConfigError("games must be at least 1")
        if self.concurrency < 1:
            raise ConfigError("concurrency must be at least 1")
        if self.max_plies < 1:
            raise ConfigError("max_plies must be at least 1")
        if self.openings.source not in ("start", "random", "file"):
            raise ConfigError(f"openings.source must be start, random or file, not {self.openings.source!r}")
        if self.openings.source == "file" and not self.openings.file:
            raise ConfigError("openings.source is 'file' but no file was given")
        if self.openings.source == "random" and self.openings.plies < 1:
            raise ConfigError("openings.plies must be at least 1")

        labels = [e.label for e in self.engines]
        if labels[0] == labels[1]:
            raise ConfigError(f"Both engines are labelled {labels[0]!r}; give them distinct name=... values")

        for e in self.resolved_engines():
            if e.depth is None and e.movetime is None and e.base is None:
                raise ConfigError(f"Engine {e.label!r} has no limit. Set depth, movetime or a clock "
                                  f"(per engine, or as a match default).")
            if e.movetime is not None and e.base is not None:
                raise ConfigError(f"Engine {e.label!r}: movetime and base/clock are mutually exclusive")
            if e.depth is not None and e.depth < 1:
                raise ConfigError(f"Engine {e.label!r}: depth must be at least 1")
            if e.movetime is not None and e.movetime <= 0:
                raise ConfigError(f"Engine {e.label!r}: movetime must be positive")
            if e.base is not None and e.base <= 0:
                raise ConfigError(f"Engine {e.label!r}: base time must be positive")
            if e.increment < 0:
                raise ConfigError(f"Engine {e.label!r}: increment cannot be negative")
