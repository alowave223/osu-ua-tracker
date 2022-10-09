#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
import os

import discord
from app.settings import Settings

from app.tracker import Tracker

__all__ = ()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.messages = True

    config = Settings()
    client = Tracker(config, intents=intents).run(
        token=config.BOT_TOKEN.get_secret_value()
    )
