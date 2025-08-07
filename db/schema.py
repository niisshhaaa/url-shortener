from pydantic import BaseModel
from sqlalchemy.orm import  declarative_base, relationship
from sqlalchemy import Column, Index , Integer , String , TIMESTAMP ,ForeignKey ,DATE,Enum, text
from datetime import datetime
import enum

#Base class for ORM models(mapped classes)
Base=declarative_base()

class TierLevel(enum.Enum):
    HOBBY='hobby'
    ENTERPRISE='enterprise'
    FREE='free'

#ORM mapped classes -->
class URL_SHORTENER(Base):
    __tablename__="url_shortener"
    id=Column(Integer,primary_key=True,autoincrement=True)
    original_url=Column(String,nullable=False)
    short_code=Column(String,nullable=False,unique=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    visit_cnt = Column(Integer,default=0,nullable=False)
    last_accessed_at=Column(TIMESTAMP,nullable=True)
    user_id = Column(Integer, ForeignKey("userss.id"),nullable=True)
    deleted_at=Column(TIMESTAMP,nullable=True)
    expiry_date=Column(DATE,nullable=True)
    password=Column(String(50),nullable=True)

    user = relationship("Users", back_populates="urls")

    __table_args__ = (
        Index("idx_created_at", created_at),
    )


    def to_dict(self):
        """
        to ensure response is serialised to json if not done already
        """
   
        return {
            "id" : self.id,
            "original_url":self.original_url,
            "short_code":self.short_code,
            "created_at":self.created_at,
            "visit_cnt":self.visit_cnt,
            "last_accessed_at":self.last_accessed_at,
            "user_id":self.user_id,
            "deleted_at":self.deleted_at,
            "expiry_date":self.expiry_date
        }

class Users(Base):
    __tablename__="userss"
    id=Column(Integer,primary_key=True,autoincrement=True)
    email=Column(String(40),nullable=False,unique=True)
    name=Column(String(20),nullable=True)
    api_key=Column(String(100),nullable=False,unique=True)
    password_hash=Column(String(255),nullable=True)  #kept nullable true as using api keys for authentication,it was just to try jwt auth
    user_inactive=Column(TIMESTAMP,nullable=True)
    created_at=Column(TIMESTAMP,default=datetime.now)
    updated_at=Column(TIMESTAMP,default=datetime.now,onupdate=datetime.now)
    tier_level=Column(Enum('HOBBY', 'ENTERPRISE','FREE', name='tierlevel', create_type=False),server_default=text("'FREE'"),nullable=False)
    #change the name of enum to lowercase as postgresql stores case sensitive names in double quotes and non case sensitive in single quotes.
    #otherwise it will cause problem when adding new user and not specifying any value for tier_level directly
    #First chnage in sqlalchemy using alembic and then update here in orm .

    def __repr__(self)->str:
        return (f"Users(id: {self.id}, email: {self.email}, name: {self.name}, "
                f"api_key: {self.api_key}, created_at: {self.created_at})")
    
    def to_dict(self, exclude_password=True):
        """
        Convert the object into a dictionary for serialization.
        Excludes password_hash unless explicitly included
        """
        user_dict = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "api_key": self.api_key,
            "user_inactive": self.user_inactive,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tier_level": self.tier_level.value,
        }
        if not exclude_password:
            user_dict["password_hash"] = self.password_hash
        return user_dict

    urls=relationship("URL_SHORTENER",back_populates="user")



