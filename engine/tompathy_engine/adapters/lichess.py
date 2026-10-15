"""PGN moves with witnessed legal alternatives and complete clock chronology."""

import io
import re
from datetime import UTC, datetime, timedelta

import chess
import chess.pgn

from ..ledger.ids import digest, maker_id, text_hash
from ..ledger.provenance import provenance_for
from ..ledger.schema import Artifact, Cost, Decision, Maker, Option, Session, StatedGoal


def ingest(pgn, ledger):
    stream = io.StringIO(pgn)
    all_rows, games, plies, evaluation_count, excluded = [], 0, 0, 0, 0
    while (game := chess.pgn.read_game(stream)) is not None:
        if game.errors:
            raise ValueError("Malformed or illegal PGN")
        games += 1
        headers = game.headers
        clock = re.fullmatch(r"(\d+)\+(\d+)", headers.get("TimeControl", ""))
        if clock is None or "UTCDate" not in headers or "UTCTime" not in headers:
            excluded += 1
            continue
        start = datetime.strptime(
            headers["UTCDate"] + " " + headers["UTCTime"], "%Y.%m.%d %H:%M:%S"
        ).replace(tzinfo=UTC)
        base, increment = map(float, clock.groups())
        nodes = list(game.mainline())
        # Missing clocks cannot be converted to invented UTC event times.
        if any(node.clock() is None for node in nodes):
            excluded += 1
            continue
        ident = digest(["lichess", headers.get("Site"), str(game)])
        makers = {}
        for side, color in (("White", chess.WHITE), ("Black", chess.BLACK)):
            label = headers.get(side)
            if not label or label == "?":
                raise ValueError("PGN needs both source player identities")
            maker = maker_id("lichess", label.casefold())
            makers[color] = maker
            all_rows.append(
                Maker(
                    maker_id=maker,
                    source_dataset="lichess",
                    identity="pseudonymous",
                    display_label=label,
                    identity_basis=["PGN player attribution"],
                )
            )
        sessions = {color: digest([ident, maker, "session"]) for color, maker in makers.items()}
        goals = {color: digest([sessions[color], "win"]) for color in makers}
        board, current, previous = game.board(), start, {chess.WHITE: base, chess.BLACK: base}
        game_rows = []
        for index, node in enumerate(nodes):
            color = board.turn
            maker = makers[color]
            remaining = float(node.clock())
            latency = previous[color] + increment - remaining
            if latency < -0.1:
                raise ValueError("Clock increased beyond the declared increment")
            latency = max(0.0, latency)
            resolved = current + timedelta(seconds=latency)
            options = [
                Option(option_id=m.uci(), origin="env", position=i)
                for i, m in enumerate(sorted(board.legal_moves, key=lambda m: m.uci()))
            ]
            evaluation = node.eval()
            evaluation_count += evaluation is not None
            outcome = {"game_result": headers.get("Result", "*"), "result_available_at": None}
            if evaluation is not None:
                outcome["post_move_engine_score"] = evaluation.pov(color).score(mate_score=100000)
            game_rows.append(
                Decision(
                    decision_id=digest([ident, index]),
                    maker_id=maker,
                    session_id=sessions[color],
                    t_open=current,
                    t_resolve=resolved,
                    options=options,
                    taken=node.move.uci(),
                    action="move",
                    cost=Cost(latency_s=latency, time_left_s=remaining),
                    context={
                        "fen": board.fen(),
                        "ply": index,
                        "clock_resolution": "PGN clock-derived",
                    },
                    outcome=outcome,
                )
            )
            current, previous[color] = resolved, remaining
            board.push(node.move)
            plies += 1
        for row in game_rows:
            row.outcome["result_available_at"] = current.isoformat()
        all_rows.extend(game_rows)
        all_rows.append(
            Artifact(
                artifact_id=ident,
                maker_ids=list(makers.values()),
                kind="game",
                source_uri=headers.get("Site", "lichess:unknown"),
                tier="T2",
                domain="chess",
            )
        )
        for color, maker in makers.items():
            all_rows.extend(
                [
                    Session(
                        session_id=sessions[color],
                        maker_id=maker,
                        artifact_id=ident,
                        t_start=start,
                        t_end=current,
                        stated_goal_ids=[goals[color]],
                    ),
                    StatedGoal(
                        goal_id=goals[color],
                        maker_id=maker,
                        scope="session",
                        scope_id=sessions[color],
                        text="Win the game",
                        source="assignment",
                        t=start,
                    ),
                ]
            )
    ledger.append_new(all_rows, provenance_for(all_rows, "lichess", text_hash(pgn)))
    return {
        "games": games,
        "excluded_missing_clock_or_time": excluded,
        "moves": plies,
        "post_move_evaluation_coverage": evaluation_count / plies if plies else None,
        "note": "Post-move engine scores and final results are outcomes, never pre-move features",
    }
