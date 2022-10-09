from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Union

from discord.utils import find
from ossapi import OssapiV2
from ossapi.enums import GameMode
from ossapi.enums import RankingType
from ossapi.enums import ScoreType
from ossapi.models import Cursor
from ossapi.models import Rankings
from ossapi.models import Score
from ossapi.models import User
from ratelimiter import RateLimiter

from app.logging import Ansi
from app.logging import log


@RateLimiter(max_calls=250, period=60)
def get_ranks(api: OssapiV2, page: int) -> Rankings:
    return api.ranking(GameMode.STD, RankingType.PERFORMANCE, "ua", Cursor(page=page))


@RateLimiter(max_calls=250, period=60)
def get_scores(api: OssapiV2, id: int) -> list[Score]:
    scores = api.user_scores(id, ScoreType.BEST, mode=GameMode.STD, limit=50)

    return scores


def update_tracklist(
    api: OssapiV2,
) -> tuple[list[tuple[User, User]], list[Score], list[Union[User, int]]]:
    log("Started update", Ansi.BLUE)

    start = time.time()
    json_path = Path("./track.json")

    new_players: list[tuple[User, User]] = []
    new_scores: list[Score] = []
    banned_players: list[Union[User, int]] = []

    track_file: list[
        dict[str, Union[str, int, dict[str, Union[str, int]]]]
    ] = json.loads(json_path.read_bytes())

    new_stats = []
    for page in range(4):
        ranks = get_ranks(api, page + 1)

        for idx, place in enumerate(ranks.ranking):
            scores = get_scores(api, place.user.id)
            country_rank = (idx + 1) + (50 * page)

            new_stats.append(
                {
                    "name": place.user.username,
                    "id": place.user.id,
                    "statistics": {
                        "crank": country_rank,
                        "grank": place.global_rank,
                        "scores": [score.id for score in scores],
                    },
                },
            )

            if track_file:
                if place.user.id not in [x["id"] for x in track_file]:
                    old_player = find(
                        lambda x: x["statistics"]["crank"] == country_rank,
                        track_file,
                    )

                    new_players.append(
                        (
                            api.user(place.user.id, GameMode.STD),
                            api.user(old_player["id"], GameMode.STD),
                        ),
                    )
                else:
                    old = find(lambda x: x["id"] == place.user.id, track_file)[
                        "statistics"
                    ]["scores"]
                    new = find(lambda x: x["id"] == place.user.id, new_stats)[
                        "statistics"
                    ]["scores"]

                    if dif_scores := list(set(new) ^ set(old)):
                        for score in dif_scores:
                            exact_score = find(lambda x: x.id == score, scores)

                            if exact_score:
                                new_scores.append(exact_score)

    if diff_users := list(
        {x["id"] for x in track_file} - {x["id"] for x in new_stats},
    ):
        for user in diff_users:
            if user not in [x.id for _, x in new_players]:
                user_api = api.user(user)

                banned_players.append(user)
                log(
                    f"Banned player: {user} | osu!Api: {user_api.is_restricted}",
                    Ansi.CYAN,
                )

    json_path.unlink()
    json_path.write_text(json.dumps(new_stats, indent=2))

    end = time.time() - start

    m, s = divmod(round(end), 60)
    h, m = divmod(m, 60)

    log(f"Done, elapsed: {h:d}:{m:02d}:{s:02d}", Ansi.BLUE)
    log(f"New Players: {len(new_players)}; New Scores: {len(new_scores)}", Ansi.YELLOW)
    return (new_players, new_scores, banned_players)
