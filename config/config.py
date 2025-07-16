from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPER_SECRET_KEY:str 
    ALGORITHM: str 
        
    model_config=SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

configSettgs=Settings()
