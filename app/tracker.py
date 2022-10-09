from __future__ import annotations

__all__ = ("Tracker",)

from app.version import Version

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import time
from typing import Optional
from discord import Embed
import discord

from ossapi import OssapiV2
from discord.ext import commands, tasks
from app.logging import Ansi, log
from app.settings import Settings

from app.usecases.updater import update_tracklist
from app.utils import rank_to_str


class Tracker(commands.Bot):
    __slots__ = ("config", "loop", "update_loop", "pool", "version", "uptime", "api")

    def __init__(self, config: Settings, **kwargs) -> None:
        super().__init__(
            command_prefix=self.when_mentioned_or_prefix(),
            help_command=None,
            **kwargs,
        )

        self.config = config
        self.pool = ThreadPoolExecutor(max_workers=2)
        self.api = OssapiV2(
            self.config.OSU_API_CLIENT_ID,
            self.config.OSU_API_CLIENT_SECRET.get_secret_value(),
        )
        self.version = Version(1, 2, 0)
        self.uptime: Optional[int] = None
        self.jezus = False

        log("Initializing discord.", Ansi.RED)

    def when_mentioned_or_prefix(self):
        def inner(bot, msg):
            prefix = "$"
            return commands.when_mentioned_or(prefix)(bot, msg)

        return inner

    async def on_ready(self) -> None:
        self.uptime = time.time()

        # Updater blocks entire loop, so our client is recconnecting constantly,
        # to prevent repetitive initialization, I made this peace of shit.
        # TODO: Make updater not block the loop
        if not self.jezus:
            log("Discord Initialized!", Ansi.GREEN)
            self.jezus = True

            self.loop = asyncio.get_event_loop()
            self.task_1.start()
            log("Updater has been started.", Ansi.MAGENTA)

    @tasks.loop(seconds=600)
    async def task_1(self) -> None:
        await self.wait_until_ready()

        self.loop.create_task(self.start_update())

    async def start_update(self) -> None:
        announce_channel = self.get_channel(self.config.ANNOUNCE_CHANNEL_ID)
        new_players, new_scores, banned_players = await self.loop.run_in_executor(
            self.pool,
            update_tracklist,
            self.api,
        )

        if new_players:
            for new_player, old_player in new_players:
                embed = Embed(
                    colour=discord.Colour.from_rgb(66, 135, 245),
                    description=f"**{new_player.username}** обійшов **{old_player.username}** й потрапив до топ-200!",
                )

                embed.set_author(
                    name="Новий гравець в топ-200!",
                    icon_url="https://sakuru.pw/static/flags/UA.png",
                )
                embed.set_thumbnail(url=new_player.avatar_url)

                embed.add_field(name="PP", value=f"{new_player.statistics.pp}pp")
                embed.add_field(
                    name="Acc",
                    value=f"{new_player.statistics.hit_accuracy:.2f}%",
                )
                embed.add_field(
                    name="Playcount",
                    value=f"{new_player.statistics.play_count}",
                )

                embed.set_footer(text="Це є мотивація")
                embed.timestamp = datetime.now()
                await announce_channel.send(embeds=[embed])

        if new_scores:
            for score in new_scores:
                score_user = self.api.user(score.user_id)
                score_bmap = self.api.beatmap(score.beatmap.id)
                score_bmap_creator = self.api.user(score.beatmapset.creator)

                embed = Embed(
                    colour=discord.Colour.from_rgb(66, 135, 245),
                    description=(
                        f"__**Новий топ-50 скор для гравця!**__\n"
                        f"**{rank_to_str(score.rank)} {'+' + str(score.mods) + ' ' if score.mods.value != 0 else ''}"
                        f"{score.score:,} ({score.accuracy * 100:.2f}%)**\n **{score.pp:.2f}pp** "
                        f"[**{score.max_combo}x**/{score_bmap.max_combo}x] "
                        f"{{{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}}}"
                    ),
                    url=score.beatmap.url,
                    title=f"{score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}] [{score.beatmap.difficulty_rating:.2f}★]",
                )

                embed.set_author(
                    name=(
                        f"{score_user.username}: {score_user.statistics.pp}pp "
                        f"(#{score_user.statistics.global_rank} UA{score_user.statistics.country_rank})"
                    ),
                    icon_url=score_user.avatar_url,
                    url=f"https://osu.ppy.sh/u/{score_user.id}",
                )
                embed.set_thumbnail(url=score.beatmapset.covers.list)

                embed.set_footer(
                    text=f"Мапа {score_bmap_creator.username}, зіграно {score.created_at.strftime('%d.%m.%Y o %H:%M')}",
                    icon_url=score_bmap_creator.avatar_url,
                )
                await announce_channel.send(embeds=[embed])

        if banned_players:
            for player in banned_players:
                await announce_channel.send(f"Banned player: {player}")
