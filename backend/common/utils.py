import socket
import string
from urllib.parse import urlparse
from fastapi import HTTPException
from passlib.context import CryptContext
import secrets,os,jwt,uuid,logging
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime ,timedelta

def check_is_date_valid(date):
        try:
            date=date
            print(date,date.date(),date.now().date(),datetime.now().date())
            print("now date",datetime.now().date())
            if isinstance(date,str):       # date from payload
                date=datetime.fromisoformat(date)
            
            if isinstance(date,datetime):  # from query parameter of update request
                date=date.date()
            
            if date>=datetime.now().date():
                return date
            else:
                raise HTTPException(status_code=400,detail="Dates before today not allowed")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expiry date format. Use YYYY-MM-DD ")