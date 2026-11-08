# Test suite

The project uses Python's built-in `unittest` framework, so no test runner
dependency is required. Install the application requirements first, then run
the complete suite from the repository root:

```powershell
python -m unittest discover -s tests -t . -v
```

Each production feature has its own test module and can be run independently:

```powershell
python -m unittest tests.test_rules -v
python -m unittest tests.test_engine_basic -v
python -m unittest tests.test_engine_current -v
```

`test_engine_basic.py` is deliberately shared by all released engine versions
(`engine_v2_1`, `engine_v2_2`, and `engine`). It checks the stable engine
contract: legal search results, simple forced mates, material comparisons, and
non-mutating search. `test_engine_current.py` covers the newer implementation
details that only the current `engine` promises: deterministic evaluation,
transposition-table search, move ordering, and quiescence handling of special
captures.

| Test module | Feature covered |
| --- | --- |
| `test_move.py` | coordinates and move representations |
| `test_pieces.py` | piece values and enums |
| `test_board.py` | board state, FEN, bitboards, copies, and undo |
| `test_zobrist.py` | incremental position hashing regressions |
| `test_rules.py` | standard/infinity rules and terminal conditions |
| `test_move_generator.py` | rules-to-board integration |
| `test_game.py` | game-session workflow and serialisation |
| `test_app.py` | Flask API validation, routing, and engine selection |
| `test_engine_basic.py` | stable contract for every engine version |
| `test_engine_current.py` | current-engine-only search features |
