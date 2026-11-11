"""
Tests for the arena (engine-vs-engine) framework.

Run from the repository root:

    python -m unittest tests.test_arena -v

Most tests use tiny fake engines (written to a temp directory and loaded through
the `root=` option) so that failure handling - illegal moves, crashes, hangs,
adjudication - can be exercised quickly and deterministically. A few tests run
the real engines at depth 1.
"""

import json
import math
import shutil
import tempfile
import textwrap
import threading
import unittest
from pathlib import Path

from arena import stats
from arena.config import (
    ConfigError, EngineConfig, MatchConfig, OpeningConfig, parse_engine_spec, parse_time_control,
)
from arena.game import GameRecord, MoveRecord, engine_seed, play_game
from arena.match import run_match
from arena.openings import (
    generate_openings, has_winning_capture, load_opening_file, material_balance, start_fen,
)
from arena.uci_client import UciEngine
from infinity_chess.board import Board
from infinity_chess.rules import InfinityChessRules

REPO_ROOT = Path(__file__).resolve().parents[1]


# ── fake engines ──────────────────────────────────────────────────────────────

_FAKE_TEMPLATE = '''
import time
from infinity_chess.move import Move, Square
from infinity_chess.move_generator import MoveGenerator


class Search:
    def __init__(self, board, rules=None, isVary=True):
        self.board, self.rules = board, rules
        self.nodes_searched = 0
        self.depth_reached = 0

    def find_best_move(self, depth, time_limit=None):
        self.nodes_searched, self.depth_reached = 1, depth
{body}
'''

_FAKE_BODIES = {
    # plays the first legal move, evaluates the position as `score`
    "engine_first":   "        moves = MoveGenerator(self.board, self.rules).legal_moves()\n        return moves[0], 0",
    "engine_losing":  "        moves = MoveGenerator(self.board, self.rules).legal_moves()\n        return moves[0], -900",
    "engine_illegal": "        return Move(Square(0, 0), Square(0, 0)), 0",
    "engine_crash":   "        raise RuntimeError('boom')",
    "engine_hang":    "        time.sleep(120)",
}


def make_fake_root() -> Path:
    """A throwaway repo root: a copy of infinity_chess plus the fake engine packages."""
    root = Path(tempfile.mkdtemp(prefix="arena_test_"))
    shutil.copytree(REPO_ROOT / "infinity_chess", root / "infinity_chess",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for name, body in _FAKE_BODIES.items():
        pkg = root / name
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "search.py").write_text(_FAKE_TEMPLATE.format(body=body))
    return root


def fake_cfg(root: Path, a: str, b: str, **kw) -> MatchConfig:
    cfg = MatchConfig(
        engines=[EngineConfig(a, name="A", root=str(root)), EngineConfig(b, name="B", root=str(root))],
        depth=1, seed=1, openings=OpeningConfig(source="start"), max_plies=40, **kw,
    )
    cfg.validate()
    return cfg


def play(cfg: MatchConfig, root: Path, a_is_white: bool = True, fen: str | None = None) -> GameRecord:
    return play_game(0, fen or start_fen(), a_is_white, cfg, cfg.resolved_engines(), root, threading.Event())


# ── statistics ────────────────────────────────────────────────────────────────

class StatsMathTests(unittest.TestCase):
    def test_elo_from_score(self):
        self.assertAlmostEqual(stats.elo_from_score(0.5), 0.0)
        self.assertAlmostEqual(stats.elo_from_score(0.75), 190.85, places=1)
        self.assertAlmostEqual(stats.elo_from_score(0.25), -190.85, places=1)
        self.assertEqual(stats.elo_from_score(1.0), math.inf)
        self.assertEqual(stats.elo_from_score(0.0), -math.inf)

    def test_equal_results_give_symmetric_interval_around_zero(self):
        elo, lo, hi = stats.elo_interval(20, 10, 20)
        self.assertAlmostEqual(elo, 0.0)
        self.assertAlmostEqual(lo, -hi, places=6)
        self.assertLess(lo, 0.0)

    def test_more_games_narrow_the_interval(self):
        _, lo1, hi1 = stats.elo_interval(15, 10, 5)
        _, lo2, hi2 = stats.elo_interval(150, 100, 50)
        self.assertLess(hi2 - lo2, hi1 - lo1)

    def test_los(self):
        self.assertAlmostEqual(stats.likelihood_of_superiority(10, 10), 0.5)
        self.assertGreater(stats.likelihood_of_superiority(30, 10), 0.99)
        self.assertEqual(stats.likelihood_of_superiority(0, 0), 0.5)

    def test_no_games(self):
        self.assertEqual(stats.score_confidence(0, 0, 0), (0.5, 0.0, 1.0))


def _record(index, a_is_white, result, reason="checkmate", moves=()):
    return GameRecord(index=index, opening=start_fen(), a_is_white=a_is_white,
                      result=result, reason=reason, moves=list(moves), duration_s=1.0)


class SummaryTests(unittest.TestCase):
    def test_score_a_follows_colours(self):
        self.assertEqual(_record(0, True, "1-0").score_a, 1.0)
        self.assertEqual(_record(0, False, "1-0").score_a, 0.0)
        self.assertEqual(_record(0, False, "0-1").score_a, 1.0)
        self.assertEqual(_record(0, True, "1/2-1/2").score_a, 0.5)

    def test_summary_counts_and_colour_split(self):
        games = [
            _record(0, True, "1-0"),                     # A white wins
            _record(1, False, "1-0"),                    # A black loses
            _record(2, True, "1/2-1/2", "repetition"),   # draw
            _record(3, False, "0-1"),                    # A black wins
        ]
        s = stats.summarize(games, ["A", "B"])
        self.assertEqual((s["a"]["wins"], s["a"]["draws"], s["a"]["losses"]), (2, 1, 1))
        self.assertEqual(s["as_white"], {"wins": 1, "draws": 1, "losses": 0})
        self.assertEqual(s["as_black"], {"wins": 1, "draws": 0, "losses": 1})
        self.assertAlmostEqual(s["a"]["score"], 0.625)
        self.assertEqual(s["terminations"], {"checkmate": 3, "repetition": 1})
        # White scored: win, win, draw, loss -> 2.5 / 4
        self.assertAlmostEqual(s["white_score"], 0.625)
        self.assertIn("A", stats.format_summary(s))

    def test_failures_are_attributed_to_the_loser(self):
        g = _record(0, True, "0-1", "illegal move")
        g.error = "A played a1a1"
        s = stats.summarize([g], ["A", "B"])
        self.assertEqual(s["failures"], {"A": 1, "B": 0})

    def test_engine_move_stats(self):
        moves = [MoveRecord(1, 0, "e2e4", depth=2, nodes=100, time_s=1.0),
                 MoveRecord(2, 1, "e7e5", depth=3, nodes=300, time_s=2.0),
                 MoveRecord(3, 0, "d2d4", depth=4, nodes=200, time_s=1.0)]
        st = stats.engine_move_stats([_record(0, True, "1/2-1/2", moves=moves)], 0)
        self.assertEqual(st["moves"], 2)
        self.assertAlmostEqual(st["avg_time_s"], 1.0)
        self.assertAlmostEqual(st["avg_nodes"], 150)
        self.assertAlmostEqual(st["nodes_per_s"], 150)
        self.assertAlmostEqual(st["avg_depth"], 3.0)

    def test_nodes_reported_as_unavailable_when_zero(self):
        moves = [MoveRecord(1, 0, "e2e4", depth=1, nodes=0, time_s=1.0)]
        st = stats.engine_move_stats([_record(0, True, "1/2-1/2", moves=moves)], 0)
        self.assertNotIn("avg_nodes", st)

    def test_overshoot(self):
        moves = [MoveRecord(i, 0, "e2e4", time_s=t) for i, t in enumerate([0.1, 0.1, 0.9, 1.5], 1)]
        frac, worst = stats.overshoot([_record(0, True, "1/2-1/2", moves=moves)], 0, 0.5)
        self.assertAlmostEqual(frac, 0.5)
        self.assertEqual(worst, 1.5)

    def test_record_roundtrip_through_json(self):
        g = _record(3, False, "0-1", moves=[MoveRecord(1, 1, "e2e4", 2, 35, None, 99, 0.5)])
        again = GameRecord.from_dict(json.loads(json.dumps(g.to_dict())))
        self.assertEqual(again, g)


# ── configuration ─────────────────────────────────────────────────────────────

class ConfigTests(unittest.TestCase):
    def test_engine_spec(self):
        e = parse_engine_spec(r"engine_v2_2:name=old,depth=4,movetime=0.5,vary=false,root=C:\code\abbott")
        self.assertEqual((e.package, e.name, e.depth, e.movetime, e.vary), ("engine_v2_2", "old", 4, 0.5, False))
        self.assertEqual(e.root, r"C:\code\abbott")
        self.assertEqual(parse_engine_spec("engine").label, "engine")
        e = parse_engine_spec("engine:tc=60+0.5")
        self.assertEqual((e.base, e.increment), (60.0, 0.5))

    def test_bad_engine_specs(self):
        for bad in ("", "engine:depth", "engine:depth=x", "engine:nonsense=1", ":depth=2"):
            with self.assertRaises(ConfigError, msg=bad):
                parse_engine_spec(bad)

    def test_time_control(self):
        self.assertEqual(parse_time_control("60+0.5"), (60.0, 0.5))
        self.assertEqual(parse_time_control("90"), (90.0, 0.0))
        with self.assertRaises(ConfigError):
            parse_time_control("fast")

    def test_defaults_fill_only_missing_limits(self):
        cfg = MatchConfig(engines=[parse_engine_spec("engine:name=a,depth=5"), parse_engine_spec("engine_v2_2:name=b")],
                          depth=3, movetime=1.0)
        a, b = cfg.resolved_engines()
        self.assertEqual((a.depth, a.movetime), (5, 1.0))
        self.assertEqual((b.depth, b.movetime), (3, 1.0))

    def test_engine_own_clock_beats_match_default_movetime(self):
        cfg = MatchConfig(engines=[parse_engine_spec("engine:name=a,tc=30+1"), parse_engine_spec("engine_v2_2:name=b")],
                          movetime=2.0)
        a, b = cfg.resolved_engines()
        self.assertEqual((a.movetime, a.base), (None, 30.0))
        self.assertEqual((b.movetime, b.base), (2.0, None))

    def test_validation_errors(self):
        two = lambda **kw: MatchConfig(engines=[parse_engine_spec("engine:name=a"), parse_engine_spec("engine_v2_2:name=b")], **kw)
        two(depth=2).validate()                                   # fine
        for bad in (
            MatchConfig(engines=[parse_engine_spec("engine")], depth=2),                      # one engine
            two(),                                                                             # no limits
            two(depth=0),
            two(depth=2, games=0),
            two(depth=2, concurrency=0),
            two(movetime=1.0, base=10.0),                                                      # both limits
            MatchConfig(engines=[parse_engine_spec("engine"), parse_engine_spec("engine")], depth=2),  # same label
        ):
            with self.assertRaises(ConfigError):
                bad.validate()

    def test_from_dict_rejects_unknown_keys(self):
        with self.assertRaises(ConfigError):
            MatchConfig.from_dict({"engines": [], "gaems": 5})
        with self.assertRaises(ConfigError):
            MatchConfig.from_dict({"engines": [{"package": "engine", "dpeth": 3}]})

    def test_from_dict_accepts_string_forms(self):
        cfg = MatchConfig.from_dict({
            "engines": ["engine:name=a", {"package": "engine_v2_2", "name": "b", "depth": 2}],
            "openings": "start", "tc": "10+0.1", "games": 6,
        })
        self.assertEqual(cfg.openings.source, "start")
        self.assertEqual((cfg.base, cfg.increment), (10.0, 0.1))
        cfg.validate()

    def test_shipped_example_configs_are_valid(self):
        for path in sorted((REPO_ROOT / "arena" / "configs").glob("*.json")):
            MatchConfig.from_json(path).validate()


# ── openings ──────────────────────────────────────────────────────────────────

class OpeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = InfinityChessRules()
        cls.book = generate_openings(60, plies=6, seed=4, max_imbalance=100)

    def test_deterministic_and_seed_dependent(self):
        self.assertEqual(self.book, generate_openings(60, 6, 4, 100))
        self.assertNotEqual(self.book, generate_openings(60, 6, 5, 100))

    def test_unique_playable_balanced_and_quiet(self):
        self.assertEqual(len({" ".join(f.split()[:4]) for f in self.book}), len(self.book))
        for fen in self.book:
            board = Board.from_fen(fen)
            legal = list(self.rules.legal_moves(board, board.turn))
            self.assertFalse(self.rules.game_over(board, legal)[0], fen)
            self.assertFalse(self.rules.is_in_check(board, board.turn), fen)
            self.assertLessEqual(abs(material_balance(board)), 100, fen)
            self.assertFalse(has_winning_capture(board, self.rules, legal), fen)
            self.assertEqual(board.hash, board.recompute_hash())

    def test_hanging_piece_is_detected(self):
        hanging = Board.from_fen("rnbqk1nr/pppp1ppp/4p3/8/7P/2P5/PP1PPPPb/RNBQKBNR w KQkq - 1 3")
        self.assertTrue(has_winning_capture(hanging, self.rules, list(self.rules.legal_moves(hanging, hanging.turn))))
        start = Board.standard()
        self.assertFalse(has_winning_capture(start, self.rules, list(self.rules.legal_moves(start, start.turn))))

    def test_exhausted_space_raises(self):
        with self.assertRaises(ConfigError):
            generate_openings(10_000, plies=1, seed=0)     # only 20 one-ply openings exist

    def test_file_loading_handles_fen_epd_and_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.epd"
            path.write_text(
                "# my book\n\n"
                "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1\n"
                'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 bm d5; id "x";\n'
            )
            fens = load_opening_file(path)
            self.assertEqual(len(fens), 2)
            self.assertTrue(fens[1].endswith("d3 0 1"))
            path.write_text("rnbqkbnr/pppppppp/8 w\n")
            with self.assertRaises(ConfigError):
                load_opening_file(path)
            with self.assertRaises(ConfigError):
                load_opening_file(Path(tmp) / "missing.epd")


# ── real engines through UCI ──────────────────────────────────────────────────

class RealEngineTests(unittest.TestCase):
    START = start_fen()

    def _best(self, package, args, timeout=60):
        with UciEngine(EngineConfig(package, vary=False), REPO_ROOT, seed=1) as eng:
            eng.new_game()
            eng.set_position(self.START, ["e2e4"])
            return eng.go(args, timeout), eng

    def test_all_three_engines_answer_a_depth_1_search_with_legal_moves_and_nodes(self):
        board = Board.from_fen(self.START)
        rules = InfinityChessRules()
        board.make_move(next(m for m in rules.legal_moves(board, board.turn) if m.to_uci() == "e2e4"))
        legal = {m.to_uci() for m in rules.legal_moves(board, board.turn)}
        for package in ("engine", "engine_v2_2", "engine_v2_1"):
            res, eng = self._best(package, "depth 1")
            self.assertIn(res.bestmove, legal, package)
            self.assertGreater(res.nodes, 0, f"{package} should report nodes")
            self.assertEqual(res.depth, 1)
            self.assertEqual(eng.caps.get("timelimit"), "1", package)

    def test_movetime_is_respected_and_reports_completed_depth(self):
        for package in ("engine", "engine_v2_2", "engine_v2_1"):
            res, _ = self._best(package, "depth 64 movetime 500")
            self.assertGreaterEqual(res.depth, 1)
            self.assertLess(res.wall_s, 4.0, f"{package} ignored its time limit")

    def test_clock_parameters_are_turned_into_a_budget(self):
        res, _ = self._best("engine", "wtime 3000 btime 3000 winc 0 binc 0")   # black to move: ~100 ms budget
        self.assertLess(res.wall_s, 3.0)

    def test_aborted_search_leaves_the_board_untouched(self):
        from engine.search import Search
        board = Board.standard()
        before = (board.to_fen(), board.hash, list(board.zobrist_history))
        s = Search(board, InfinityChessRules(), isVary=False)
        move, _ = s.find_best_move(30, time_limit=0.3)
        self.assertIsNotNone(move)
        self.assertEqual((board.to_fen(), board.hash, list(board.zobrist_history)), before)
        self.assertEqual(board.hash, board.recompute_hash())

    def test_no_time_limit_means_exactly_the_requested_depth(self):
        from engine.search import Search
        s = Search(Board.standard(), InfinityChessRules(), isVary=False)
        s.find_best_move(2)
        self.assertEqual(s.depth_reached, 2)
        self.assertGreater(s.nodes_searched, 0)

    def test_seed_makes_noisy_engines_repeatable(self):
        def run():
            with UciEngine(EngineConfig("engine", vary=True), REPO_ROOT, seed=123) as eng:
                eng.new_game()
                eng.set_position(self.START, [])
                r = eng.go("depth 2", 60)
                return r.bestmove, r.score_cp
        self.assertEqual(run(), run())


# ── referee behaviour with fake engines ───────────────────────────────────────

class RefereeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = make_fake_root()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_illegal_move_loses_for_either_colour(self):
        cfg = fake_cfg(self.root, "engine_illegal", "engine_first")
        for a_white in (True, False):
            rec = play(cfg, self.root, a_is_white=a_white)
            self.assertEqual(rec.reason, "illegal move")
            self.assertEqual(rec.score_a, 0.0, f"A white={a_white}")
            self.assertIn("a1a1", rec.error)

    def test_crash_loses_and_reports_stderr(self):
        rec = play(fake_cfg(self.root, "engine_first", "engine_crash"), self.root)
        self.assertEqual(rec.reason, "engine crash")
        self.assertEqual(rec.score_a, 1.0)
        self.assertIn("boom", rec.error)

    def test_hang_is_killed_after_move_timeout(self):
        cfg = fake_cfg(self.root, "engine_hang", "engine_first", move_timeout=2.0)
        rec = play(cfg, self.root, a_is_white=True)
        self.assertEqual(rec.reason, "engine timeout")
        self.assertEqual(rec.score_a, 0.0)
        self.assertLess(rec.duration_s, 20)

    def test_resign_adjudication_uses_the_engines_own_score(self):
        cfg = fake_cfg(self.root, "engine_losing", "engine_first", resign_cp=500, resign_moves=2)
        rec = play(cfg, self.root, a_is_white=True)
        self.assertEqual(rec.reason, "adjudicated resignation")
        self.assertEqual(rec.score_a, 0.0)
        self.assertEqual(len(rec.moves), 3)           # A moved twice (plies 1 and 3)

    def test_draw_adjudication(self):
        cfg = fake_cfg(self.root, "engine_first", "engine_first", draw_cp=20, draw_moves=1, draw_after=2)
        rec = play(cfg, self.root)
        self.assertEqual((rec.result, rec.reason), ("1/2-1/2", "adjudicated draw"))
        self.assertEqual(len(rec.moves), 2)

    def test_max_plies(self):
        cfg = fake_cfg(self.root, "engine_first", "engine_first")
        cfg.max_plies = 3
        rec = play(cfg, self.root)
        self.assertEqual(len(rec.moves), 3)
        self.assertIn(rec.reason, ("max plies", "repetition"))

    def test_movetime_and_clock_plumbing(self):
        cfg = fake_cfg(self.root, "engine_first", "engine_first")
        cfg.max_plies = 4
        cfg.depth, cfg.movetime = None, 0.2
        self.assertEqual(len(play(cfg, self.root).moves), 4)
        cfg.movetime, cfg.base, cfg.increment = None, 30.0, 1.0
        rec = play(cfg, self.root)
        self.assertEqual(len(rec.moves), 4)
        self.assertEqual(rec.error, "")

    def test_flag_fall_is_loss_on_time(self):
        cfg = fake_cfg(self.root, "engine_hang", "engine_first")
        cfg.depth, cfg.base, cfg.increment = None, 1.0, 0.0
        rec = play(cfg, self.root, a_is_white=True)
        self.assertEqual(rec.reason, "loss on time")
        self.assertEqual(rec.score_a, 0.0)

    def test_stop_event_aborts_the_game(self):
        from arena.game import GameAborted
        cfg = fake_cfg(self.root, "engine_first", "engine_first")
        stop = threading.Event()
        stop.set()
        with self.assertRaises(GameAborted):
            play_game(0, start_fen(), True, cfg, cfg.resolved_engines(), self.root, stop)

    def test_seeds_differ_per_engine_and_game_but_are_stable(self):
        self.assertEqual(engine_seed(7, 3, 0), engine_seed(7, 3, 0))
        self.assertNotEqual(engine_seed(7, 3, 0), engine_seed(7, 3, 1))
        self.assertNotEqual(engine_seed(7, 3, 0), engine_seed(7, 4, 0))


# ── whole match ───────────────────────────────────────────────────────────────

class MatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = make_fake_root()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def _run(self, cfg, out):
        return run_match(cfg, REPO_ROOT, log=lambda s: None, out_dir=Path(out))

    def test_paired_openings_alternate_colours_and_results_are_saved(self):
        cfg = fake_cfg(self.root, "engine_first", "engine_first", games=4, concurrency=2)
        cfg.openings = OpeningConfig(source="random", plies=4)
        cfg.max_plies = 8
        with tempfile.TemporaryDirectory() as out:
            records, summary, folder = self._run(cfg, out)
            records.sort(key=lambda r: r.index)
            self.assertEqual(len(records), 4)
            self.assertEqual([r.a_is_white for r in records], [True, False, True, False])
            self.assertEqual(records[0].opening, records[1].opening)
            self.assertEqual(records[2].opening, records[3].opening)
            self.assertNotEqual(records[0].opening, records[2].opening)

            lines = (folder / "games.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), 4)
            self.assertEqual({json.loads(l)["index"] for l in lines}, {0, 1, 2, 3})
            saved = json.loads((folder / "config.json").read_text())
            self.assertEqual(saved["config"]["seed"], 1)
            self.assertEqual(summary["games"], 4)
            self.assertTrue((folder / "summary.txt").read_text().strip())

    def test_same_seed_gives_same_openings(self):
        def openings(seed):
            cfg = fake_cfg(self.root, "engine_first", "engine_first", games=2)
            cfg.seed, cfg.max_plies = seed, 2
            cfg.openings = OpeningConfig(source="random", plies=4)
            with tempfile.TemporaryDirectory() as out:
                records, _, _ = self._run(cfg, out)
            return sorted((r.index, r.opening) for r in records)
        self.assertEqual(openings(5), openings(5))
        self.assertNotEqual(openings(5), openings(6))

    def test_openings_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "book.epd"
            book.write_text("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1\n")
            cfg = fake_cfg(self.root, "engine_first", "engine_first", games=2)
            cfg.openings, cfg.max_plies = OpeningConfig(source="file", file=str(book)), 2
            records, _, _ = self._run(cfg, Path(tmp) / "out")
            self.assertTrue(all(r.opening.startswith("rnbqkbnr/pppppppp/8/8/4P3") for r in records))

    def test_unpaired_openings_are_independent(self):
        cfg = fake_cfg(self.root, "engine_first", "engine_first", games=2, pair_openings=False)
        cfg.openings, cfg.max_plies = OpeningConfig(source="random", plies=4), 2
        with tempfile.TemporaryDirectory() as out:
            records, _, _ = self._run(cfg, out)
        self.assertNotEqual(records[0].opening, records[1].opening)

    def test_time_limit_is_refused_for_engines_that_cannot_honour_it(self):
        # an engine whose find_best_move has no time_limit parameter
        (self.root / "engine_notime").mkdir(exist_ok=True)
        (self.root / "engine_notime" / "__init__.py").write_text("")
        (self.root / "engine_notime" / "search.py").write_text(textwrap.dedent('''
            from infinity_chess.move_generator import MoveGenerator
            class Search:
                def __init__(self, board, rules=None):
                    self.board, self.rules = board, rules
                def find_best_move(self, depth):
                    return MoveGenerator(self.board, self.rules).legal_moves()[0], 0
        '''))
        cfg = fake_cfg(self.root, "engine_notime", "engine_first")
        cfg.depth = None
        cfg.engines[0].movetime = 1.0
        cfg.engines[1].depth = 1
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ConfigError):
                self._run(cfg, out)
        # ...but fixed depth is fine
        cfg = fake_cfg(self.root, "engine_notime", "engine_first", games=2)
        cfg.max_plies = 2
        with tempfile.TemporaryDirectory() as out:
            records, _, _ = self._run(cfg, out)
        self.assertEqual(len(records), 2)

    def test_missing_engine_package_is_reported_before_any_game(self):
        from arena.uci_client import EngineStartupError
        cfg = fake_cfg(self.root, "engine_does_not_exist", "engine_first")
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(EngineStartupError):
                self._run(cfg, out)
            self.assertFalse((Path(out) / "games.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
