from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPER_SECRET_KEY:str 
    ALGORITHM: str
    REDIS_MAX_MEMORY:str
    REDIS_MEMORY_POLICY:str 
    REDIS_HOST:str
    REDIS_PORT:int
    REDIS_DB:int
    PROFILE_IMG_PATH:str
    THUMBNAIL_IMG_PATH:str
    MEDIA_ROOT:str
        
    model_config=SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

configSettgs=Settings()
