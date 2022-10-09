from pydantic import BaseSettings, Field, SecretStr

class Settings(BaseSettings):
  BOT_TOKEN: SecretStr = Field(..., env="BOT_TOKEN")
  OSU_API_CLIENT_ID: int = Field(..., env="OSU_API_CLIENT_ID")
  OSU_API_CLIENT_SECRET: SecretStr = Field(..., env="OSU_API_CLIENT_SECRET")
  ANNOUNCE_CHANNEL_ID: str = Field(..., env="ANNOUNCE_CHANNEL_ID")

  class Config:
    env_prefix = ""
    env_file = '.env'
    env_file_encoding = 'utf-8'
