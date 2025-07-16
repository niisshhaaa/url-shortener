"""User Routes ---->"""
""" JWT Tokens not utilised in routes ,api key is used for this project """

# # async def user_exists(email,session):
# #     user=await get_user(email,session)
# #     return True if user else False

# async def get_user(email:str,session):
#     stmt=select(Users.id,Users.email,Users.api_key,Users.created_at,Users.password_hash,Users.tier_level).where(Users.email==email)
#     result=await session.execute(stmt)
#     return result.first()


# # async def user_exists_get_key(email,session):
# #     user=await get_user(email,session)

# #     if user.email and user.api_key:
# #         if not user.password_hash:
# #             apiKey=user.api_key
# #             return user.api_key
# #         return None
    
# #     apiKey=None
# #     return (apiKey,)

# async def user_exists_get_key(email,session):
#     """also include user.api_key for checking to be consistent with old schema
#        api key won't be deleted to ensure backward compatibility for this project
#     """
#     user=await get_user(email,session)
#     print("user",user)
#     print("getkey",user.email)
#     print('passhash',user.password_hash)
#     print("tierle",user.tier_level)
     
#     if user.email and user.api_key:
#         """the below condition will be removed after existing accounts update/add passwords"""
#         if not user.password_hash:
#             return user.api_key
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Account already exists with this email")
    
#     return None



# async def create_user(userData:UserCreateModel,session,apiKey):
#     pass_hash=gen_password_hash(userData.password)
    
#     new_user=Users(name=userData.username,email=userData.email,password_hash=pass_hash,api_key=apiKey)

#     try:
#         session.add(new_user)
#         await session.commit()
#         await session.refresh(new_user)
#         return new_user
#     except IntegrityError:
#         await session.rollback()
#         raise HTTPException(status_code=410,detail='User with this email already exists')
#     except Exception as e:
#         await session.rollback()
#         raise e
    

# async def add_password(userData:UserCreateModel,session):
#     pass_hash=gen_password_hash(userData.password)

#     try:
#         stmt=update(Users).where(Users.email==userData.email).values(password_hash=pass_hash).returning(Users.id,Users.email,Users.password_hash)
#         result=await session.execute(stmt)
#         await session.commit()
#         return result.first()
#     except IntegrityError:
#         await session.rollback()
#         raise HTTPException(status_code=410,detail='User with this email already exists')
#     except Exception as e:
#         await session.rollback()
#         raise e




# #we can deactivate the accounts of user who don't migrate to new authentication method within given time duration

# @app.post("/user/signup",status_code=status.HTTP_201_CREATED)
# async def create_user_account(userCreatePayload:UserCreateModel,db_session:AsyncSession=Depends(get_session)):
#     email=userCreatePayload.email
#     print("signupemail",email)
    
#     try:
#         userExistsKey=await user_exists_get_key(email,db_session)

#         if userExistsKey:
#             userWithPass=await add_password(userCreatePayload,db_session)
#             return {"message":"Account created successfully!"}
        
#         new_api_key = generate_api_key()
#         new_user = await create_user(userCreatePayload, db_session, new_api_key)
#         return {"message":"Account created successfully!"}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         await db_session.rollback()
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    


# @app.post("/user/login")
# async def login_user(loginPayload:LoginInput,db_session:AsyncSession=Depends(get_session)):
#     user=await get_user(loginPayload.email,db_session)

#     if not user :
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="No account exists for this email")
    
#     isPassValid=verify_pass(loginPayload.password,user.password_hash)
#     print(isPassValid)
#     if not isPassValid:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Password is incorrect")
    
#     access_token=create_token(userIdentity={'email':user.email,'user_id':user.id})
#     refresh_token=create_token(userIdentity={'email':user.email,'user_id':user.id},refresh=True)
#     return {"message":"Login successful","access_token":access_token,"refresh_token":refresh_token,"user":{'email':user.email,'user_id':user.id}}

# @app.get("/health",status_code=200)
# async def check_connection_health(db_session:AsyncSession=Depends(get_session)):
#     try:
#         await db_session.execute(select(URL_SHORTENER.id).where(URL_SHORTENER.id==1))
#         return {"status": "healthy","detailss":"server is running smoothly and database is connected"}
#     except Exception as e:
#         return {"status":"unhealthy","details":str(e)}
    
        
# @app.get("/refresh-token")
# async def refresh_newtoken(jwtToken:dict=Depends(refreshTokenBearer)):
#     expiry=jwtToken["exp"]
#     if datetime.fromtimestamp(expiry)>datetime.now():
#         new_token=create_token(jwtToken,refresh=True)
#         return {"new_token":new_token}
    
#     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,details="Expired Token")
