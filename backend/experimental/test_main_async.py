
# # from .main_no_orm import app
# from .main import app
# import pytest
# from httpx import ASGITransport, AsyncClient
# from asgi_lifespan import LifespanManager
# import pytest
# from sqlalchemy.ext.asyncio import AsyncEngine





# @pytest.mark.anyio
# async def test_post():
#     async with LifespanManager(app):
#          input_url="https://example.com"
#          async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#             post_response=await ac.post('/shorten',json={"url_link":input_url,"custome_slug":None})
#             assert post_response.status_code == 200 
#             post_res=post_response.json()
#             assert post_res is not None
#             print(post_res)
#             short_url=post_res["short_url"]
#             print("short url",short_url)
#             short_code=short_url
    
       
#             response2=await ac.post('/shorten',json={"url_link":input_url,"custome_slug":None})
#             assert response2.status_code == 200
#             res2_short_code=response2.json()["short_url"]
#             assert res2_short_code is not None
#             assert short_code == res2_short_code

          
# @pytest.mark.anyio      
# async def test_get():  
#        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#             short_code="1e1052"
#             input_url="https://grafana.com/docs/k6/latest/extensions/"
#             get_response=await ac.get(f'/redirect?short_code={short_code}',follow_redirects=False)
#             assert get_response.status_code == 307
#             get_res=get_response.headers["Location"]
#             assert get_res==input_url
            
#             incorrect_scode="codedoesnotexist"
#             get_response2=await ac.get(f'/redirect?short_code={incorrect_scode}',follow_redirects=False)
#             assert get_response2.status_code == 404
#             assert get_response2.json()== {"detail":"URL not found"}

# @pytest.mark.anyio      
# async def test_del():
#        async with LifespanManager(app):  
#            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
# #             code_to_delete='8bcc71'
# #             del_response=await ac.delete(f'/shorten/{code_to_delete}')
# #             assert del_response.status_code==200
# #             assert del_response.json()== {"message": f"{code_to_delete} short code has been deleted"}

#                 incorrect_scode="incorrect_code"
#                 response = await ac.delete(f"/shorten/{incorrect_scode}")
#                 assert response.status_code == 404
#                 assert response.json()=={"detail":"Not a valid short code"}

   

# # it was fixed later,both tests are passed properly

# # trio tests pass only when engine.dispose is used ,
# # asyncio tests will still pass without it when all the requests are under same function 
# # if different functions for different test requests then even asyncio ones would fail after first test so again engine.dispose should be used
# # also when tests included for requests in which exceptions are raised , trio don't pass them even with engine.dispose ,use poolclass=NullPool for that

# # as per docs -- for AsyncEngine created in function scope, close and
# # clean-up pooled connections
# #await engine.dispose()