# arena: engine-vs-engine testing

Play two versions of the engine against each other and find out how much stronger one is.

* Local development tool. Not imported by `app.py`, not needed on Render. Standard library only, so nothing to add to `requirements.txt`.
* Each engine runs in its **own process** and talks to the arena in a UCI-style text protocol (details below), so engines cannot interfere with each other and a hung engine can simply be killed.
* The arena is the **referee**: it checks every move against the real rules, keeps the clocks and decides the result.

Run everything from the repository root. On Windows use your venv's Python, e.g. `.\.venv\Scripts\python.exe -m arena ...`.

## Quick start

```bash
# 40 games, both engines searching exactly 3 plies, 4 games at a time
python -m arena run --engine engine:name=v2.3 --engine engine_v2_2:name=v2.2 --depth 3 -n 40 -j 4

# same engines, 3 seconds per move
python -m arena run --engine engine:name=v2.3 --engine engine_v2_2:name=v2.2 --movetime 3 -n 40 -j 3

# whole-game clock: 2 minutes + 1 second per move
python -m arena run --engine engine:name=v2.3 --engine engine_v2_2:name=v2.2 --tc 120+1 -n 20 -j 3

# from a config file (command-line flags override it)
python -m arena run --config arena/configs/depth_match.json -n 10
```

`--engine PACKAGE[:key=value,...]` is given twice. `PACKAGE` is any folder at the repo root that contains a `search.py` (`engine`, `engine_v2_2`, and any future `engine_v2_4`, with no registration step). Keys: `name`, `depth`, `movetime`, `tc`, `base`, `inc`, `vary`, `root`.

Press **Ctrl+C** at any time: engines are shut down and the games finished so far are summarised and saved.

## What you get

```
======================================================================
v2.3  vs  v2.1      (8 games)
======================================================================
v2.3                   wins    7   draws    1   losses    0      score 93.8%
Elo difference (v2.3 - v2.1): +470   95% interval [+267, +inf]
Likelihood of superiority: 99.6%  (chance v2.3 is truly stronger; draws ignored)

v2.3 as White: +3 =1 -0     as Black: +4 =0 -0     (White scores 43.8% overall)
Game length: avg 30 plies (min 6, max 52)      total play time 15.55s
Endings: checkmate 7, repetition 1

Per-move analytics
                        moves  avg time      p95      max   avg nodes   nodes/s  avg depth
v2.3                      120      92ms    247ms    1.17s         147     1,600       1.00
v2.1                      117      29ms     58ms     82ms          15       524       1.00
```

| Line | Meaning |
|---|---|
| wins / draws / losses, score | From the first engine's point of view. Score = (wins + draws/2) / games. |
| Elo difference + interval | Elo gap implied by the score, with a 95% interval. **If the interval contains 0 you cannot yet tell the engines apart**: play more games. |
| Likelihood of superiority | Probability the first engine is really stronger, from wins vs losses (draws ignored). |
| as White / as Black | Splits results by colour. A big gap means colour matters more than the engines. |
| Endings | checkmate, stalemate, repetition, fifty-move rule, insufficient material, max plies, adjudications, and failures (loss on time, illegal move, engine crash, engine timeout). |
| avg time / p95 / max | Wall time per move as measured by the arena. |
| avg nodes, nodes/s | Search effort and speed, as reported by the engine. See the caveat about node counting below. |
| avg depth | Deepest *completed* iteration. In timed matches this shows how deep each engine actually got. |

**How many games?** With ~30% draws, 100 games resolves roughly ±57 Elo, 400 games ±28 Elo, 1000 games ±18 Elo. Python engines are slow, so budget real time: depth 3+ takes minutes per game.

### Output files

Every run writes `arena/results/<name>_<timestamp>/` (git-ignored):

| File | Contents |
|---|---|
| `config.json` | Resolved configuration, **including the seed that was used** |
| `games.jsonl` | One line per finished game: start FEN, every move with depth, score, nodes, time |
| `summary.json`, `summary.txt` | The report |

```bash
python -m arena report arena/results/<run>              # re-print the summary (works on interrupted runs too)
python -m arena replay arena/results/<run> --game 7     # move-by-move table + final position FEN
```

`replay` prints the start FEN and final FEN so you can paste either into your Infinity Chess page.

## Limits and time controls

Every engine has its own limits, so you can test asymmetric setups (depth 4 vs depth 3, or time odds). Put them on the `--engine` spec, or set match-wide defaults with `--depth`, `--movetime`, `--tc`.

| Setting | Meaning |
|---|---|
| `depth=N` | Max search depth. Alone: always exactly N. With a time limit: a ceiling. |
| `movetime=S` | Fixed seconds per move. The engine stops itself when the time is up. |
| `tc=BASE+INC` (or `base`, `inc`) | Game clock in seconds, e.g. `tc=60+0.5`. The engine budgets its own clock (`remaining / 30 + 0.8 * increment`, never more than half the clock). The arena enforces flag fall: running out of time loses the game. |

`movetime` and a clock cannot be combined on one engine. Examples:

```bash
# time odds: does v2.3 at half the time still beat v2.2?
python -m arena run --engine engine:name=v2.3,movetime=1.5 --engine engine_v2_2:name=v2.2,movetime=3 -n 40 -j 3

# unequal depth
python -m arena run --engine engine:name=d4,depth=4 --engine engine:name=d3,depth=3 -n 40 -j 4
```

Safety net: an engine that does not answer is killed and loses (`move_timeout`, default 600 s, applies to engines that have no time limit; timed engines are killed at 3 x movetime + 5 s or at clock + 1 s).

> **Read this before using short time limits.** The engines cannot stop in the middle of depth 1, and in a busy middlegame a depth-1 search (with quiescence) can take over a second in Python. So at e.g. 0.3 s per move the engines overshoot constantly, sit at depth 1, and the match degenerates into "depth 1 vs depth 1". The report prints a **NOTE** when an engine exceeds its movetime on more than 10% of moves. Use 2-3 s/move or more, or clocks of a few minutes. (A cheap future engine improvement: return the best root move found so far if depth 1 itself runs out of time.)

## Openings

Infinity Chess has no opening theory, and wrapping changes the tactics from move one, so a normal chess book would mislead. The default is **random balanced openings**: 6 random legal half-moves from the start position, kept only if

* the game is not over and the side to move is not in check,
* material is within 100 cp (`--max-imbalance`), and
* the side to move has **no winning capture** (nothing is left hanging; otherwise the opening decides the game rather than the engines).

Openings are unique, deterministic for a given `--seed`, and **paired**: each opening is played twice with colours swapped, which cancels most opening bias. Turn pairing off with `--no-pairs`.

```bash
--openings random              # default; --opening-plies 6 --max-imbalance 100
--openings start               # always the normal start position
--openings arena/openings/random6.epd     # your own list: one FEN or EPD per line, # for comments
```

Build a big reusable book (about 10 ms per opening; 10,000 takes ~2 minutes):

```bash
python -m arena openings --count 10000 --plies 6 --seed 1 --out arena/openings/random6.epd
```

Use an **even** number of plies so White is to move. If you play from the start position with `vary=false`, deterministic engines will repeat the same game; keep openings on.

## Reproducibility

`--seed N` fixes the openings and seeds each engine's random evaluation noise (`isVary`). With depth limits and the same seed, a match is repeatable. With time limits it cannot be exactly repeatable (timing varies). Each engine gets a fresh process and a fresh transposition table for every game, and a fresh `Search` for every move, matching how `app.py` behaves.

## Comparing against an older commit

`root=` points one engine at a different checkout, so you can pit your working copy against any commit **including changes to shared modules**:

```bash
git worktree add ../abbott-v2.3-worktree v2.3          # a second checkout of the v2.3 branch
python -m arena run \
    --engine engine:name=working-copy \
    --engine engine:name=v2.3-release,root=../abbott-v2.3-worktree \
    --depth 3 -n 100 -j 4
```

The referee always uses the current checkout's rules; each engine process loads its own `infinity_chess` from its root. Older commits that predate the time-limit support only run with `depth=` (the arena refuses a time limit for them with a clear message).

## Configuration reference (JSON)

See `arena/configs/` for ready-made examples (`depth_match`, `movetime_match`, `clock_match`, `time_odds`, `vs_old_commit`).

```jsonc
{
  "name": "label for the output folder",
  "games": 40,                 "concurrency": 4,        "seed": 1234,
  "engines": [ { "package": "engine", "name": "v2.3", "depth": 3, "movetime": null,
                 "base": null, "increment": 0, "vary": true, "root": null }, { ... } ],
  "depth": null, "movetime": null, "tc": "60+0.5",      // match-wide defaults for engines that set none
  "openings": { "source": "random|start|file", "file": null, "plies": 6, "max_imbalance": 100 },
  "pair_openings": true,
  "max_plies": 300,            // draw when reached
  "move_timeout": 600,
  "resign_cp": null, "resign_moves": 4,                 // adjudicate a loss on own score <= -resign_cp for N moves
  "draw_cp": null, "draw_moves": 8, "draw_after": 80,   // adjudicate a draw when both stay within +-draw_cp
  "output_dir": "arena/results"
}
```

All durations are seconds. Adjudication is off by default; it uses the engines' own scores, so use conservative values (e.g. `resign_cp: 1500`).

**Concurrency:** engines are single-threaded Python. Keep `-j` at or below your CPU core count (the arena warns if not), otherwise engines steal CPU from each other and timings (and any timed result) are distorted.

## Engine contract (adding `engine_v2_4`)

A new engine is a folder with a `search.py` exposing:

```python
class Search:
    def __init__(self, board, rules=None, isVary=True): ...      # isVary is optional
    def find_best_move(self, depth, time_limit=None): ...        # -> (Move | None, score)
    # after the call (both optional, but give the arena something to report):
    nodes_searched: int      # nodes visited by that search, whole tree
    depth_reached: int       # deepest completed iteration
```

* `score` is centipawns from the **side to move's** view (negamax); mate is `+-(MATE_SCORE - plies)`.
* `time_limit` is a soft limit in seconds. When it expires the unfinished iteration is abandoned and the best move from the last completed depth is returned. Depth 1 always completes. Engines without `time_limit` still work with `depth=`.
* Copy the patterns in `engine/search.py`: a private `_SearchTimeout` exception, the deadline check at the top of `_negamax` / `_quiescence`, and `try/finally` around `make_move` / `unmake_move` so an abort cannot leave the board corrupted.
* Engines that create a `Search` object per node (v2.1, v2.2) share one counter/deadline object between the root and its children (see `_SharedState`).

### The protocol (what `uci_server.py` speaks)

Standard UCI minus the parts that make no sense here, plus one extension. Handy for poking at an engine by hand: `python arena/uci_server.py --engine engine`.

```
uci | isready | ucinewgame | quit
setoption name Vary value true|false      setoption name Seed value N      setoption name Horizon value N
position startpos|fen <FEN> [moves e2e4 e7e5 ...]
go [depth N] [movetime MS] [wtime MS btime MS winc MS binc MS movestogo N]
-> info depth D score cp S|mate M nodes N time MS nps X pv MOVE
-> bestmove MOVE
-> info string caps timelimit=0|1          (extension, sent during the handshake)
```

Moves are coordinate notation (`e2e4`, `e7e8q`). There is no `stop`: the search is synchronous and the arena kills the process on timeout.

## Caveats worth knowing

* **Node counts are only comparable between engines that count the same way.** After the patches, v2.1 counts main-search nodes (it has no quiescence search), while v2.2/v2.3 count main-search and quiescence nodes. An *unpatched* older checkout (via `root=`) counts main-search nodes only, so its nodes/s looks ~10x lower than it really is. Compare time, depth reached and results across versions; compare node counts within a version.
* The referee applies this repo's draw rules. `StandardRules._is_threefold_repetition` returns true when the position has occurred **twice** (`count(current) >= 2` and the current position is already in the history), so games are drawn on the *second* occurrence despite the name/docstring. That inflates draw counts a little; it affects both engines equally.
* Elo from a self-play match measures strength *relative to the opponent and settings tested*, not an absolute rating.

## Tests

```bash
python -m unittest tests.test_arena -v
```

About 50 tests, ~25 s. They cover the statistics, config parsing, opening generation, the UCI layer against the real engines, and the referee's failure handling (illegal moves, crashes, hangs, flag fall, adjudication) using tiny fake engines.

## Layout

```
arena/
  cli.py          command line (run, openings, report, replay)
  config.py       EngineConfig / MatchConfig, spec + time-control parsing, validation
  match.py        runs a whole match: probe engines, schedule games, save results, Ctrl+C
  game.py         the referee: one game, rules, clocks, adjudication, records
  uci_client.py   controls one engine subprocess (reader threads, timeouts)
  uci_server.py   the engine-side UCI wrapper (standalone; supports root=)
  openings.py     random balanced openings, FEN/EPD files
  stats.py        W/D/L, Elo + interval, LOS, per-engine analytics, report text
  configs/        example JSON configs
```
