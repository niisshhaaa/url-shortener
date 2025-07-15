from fastapi import FastAPI
import random
import secrets,asyncio,os
from __init__ import app
from fastapi import HTTPException,Depends
from .schema import Users,URL_SHORTENER
from dotenv import load_dotenv
from sqlalchemy import select,delete,func,update
from db.conn_session import async_session

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

def generate_api_key():
    return secrets.token_urlsafe(32)  # Generates a 43-character base64 string(A-Z,a-z,0-9)


async def create_user(email,name=None,session=None):
    if not session:
        raise ValueError("session not available")
    print('session active')
    # Check if user with this email already exists
    stmt = select(Users).where(Users.email == email)
    result = await session.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        print(f"User with email {email} already exists. Skipping.")
        return None
    api_key=generate_api_key()
    new_user=Users(email=email,name=name,api_key=api_key)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {"user_id":new_user.id,"api_key":new_user.api_key}

def generate_user_data(count=10):
    colors = ["red", "pink", "yellow", "blue", "green", "purple", "orange", "cyan", "magenta", "indigo", 
              "violet", "crimson", "azure", "coral", "golden"]
    suffixes = ["star", "moon", "sun", "light", "sky", "wave", "cloud", "storm", "rain", "wind"]
    decorators = ["bright", "dark", "shiny", "mystic", "cosmic"]
    
    users_data = []
    used_combinations = set()
    
    while len(users_data) < count:
        decorator = random.choice(decorators)
        color = random.choice(colors)
        suffix = random.choice(suffixes)
        
        # Create email and name
        name_parts = [decorator, color, suffix]
        name = "".join(name_parts)
        email = f"{name.lower()}@starescape.com"
        
        # Ensure uniqueness
        if email not in used_combinations:
            used_combinations.add(email)
            users_data.append({"email": email, "name": name})
    
    return users_data

async def sample_users(session,count=14):  # Default to original 4 + 10 new users
    users = []
    user_data = generate_user_data(count)
    for user in user_data:
        new_userdata = await create_user(email=user["email"], name=user["name"], session=session)
        if new_userdata:
            users.append(new_userdata)
    print("users", users)
    return users 

# To get all users from db 
async def get_users(session):
    stmt = select(Users)
    result = await session.execute(stmt)
    return result.scalars().all()
    

async def main():
    if app is None:
        raise RuntimeError("FastAPI app is not initialized!")
    if async_session is None:
        raise RuntimeError("async_session is not initialized!")

    async with async_session() as session:
        # Create 14 users (original 4 + 10 new ones) and get all users after seeding
        users = await sample_users(session, 14)
        print("All users in DB after seeding:", users)

if __name__ == "__main__":
    asyncio.run(main())
    print("Sample users seeded successfully!")




