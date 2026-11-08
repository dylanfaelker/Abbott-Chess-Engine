"""Flask API tests, kept isolated from real engine search costs with mocks."""

import importlib.util
import unittest
from unittest.mock import patch

from infinity_chess.move import Move, Square


FLASK_STACK_AVAILABLE = importlib.util.find_spec("flask") is not None and importlib.util.find_spec("flask_cors") is not None


@unittest.skipUnless(FLASK_STACK_AVAILABLE, "Flask runtime dependencies are not installed")
class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global app_module
        import app as app_module

        app_module.app.config.update(TESTING=True)

    def setUp(self) -> None:
        self.client = app_module.app.test_client()
        self.starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def test_health_reports_ok(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_move_rejects_missing_or_invalid_fen(self) -> None:
        missing = self.client.post("/move", json={})
        invalid = self.client.post("/move", json={"fen": "not-a-fen"})

        self.assertEqual(missing.status_code, 400)
        self.assertEqual(missing.get_json()["error"], "Missing required field: fen")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.get_json()["error"], "Invalid FEN string")

    def test_default_engine_response_clamps_depth_and_serializes_move(self) -> None:
        constructed = []

        class FakeSearch:
            def __init__(self, board, rules) -> None:
                constructed.append((board, rules))

            def find_best_move(self, depth: int):
                self.depth = depth
                return Move(Square.from_algebraic("e2"), Square.from_algebraic("e4")), 125

        with patch.object(app_module, "Search", FakeSearch):
            response = self.client.post("/move", json={"fen": self.starting_fen, "depth": 99})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"move": "e2e4", "eval": 1.25, "depth": 8, "engine": "v2.3"},
        )
        self.assertEqual(len(constructed), 1)

    def test_version_selector_routes_to_requested_legacy_engine(self) -> None:
        class FakeV21Search:
            def __init__(self, board, rules) -> None:
                pass

            def find_best_move(self, depth: int):
                return Move(Square.from_algebraic("b1"), Square.from_algebraic("c3")), 0

        with patch.object(app_module, "Search_v2_1", FakeV21Search):
            response = self.client.post("/move", json={"fen": self.starting_fen, "engine": "v2.1", "depth": 0})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["engine"], "v2.1")
        self.assertEqual(response.get_json()["move"], "b1c3")
        self.assertEqual(response.get_json()["depth"], 1)

    def test_engine_without_a_legal_move_returns_client_error(self) -> None:
        class NoMoveSearch:
            def __init__(self, board, rules) -> None:
                pass

            def find_best_move(self, depth: int):
                return None, 0

        with patch.object(app_module, "Search", NoMoveSearch):
            response = self.client.post("/move", json={"fen": self.starting_fen})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "No legal moves available")


if __name__ == "__main__":
    unittest.main()
