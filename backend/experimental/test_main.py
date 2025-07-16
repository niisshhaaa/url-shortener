# from fastapi.testclient import TestClient 
# from fastapi.responses import RedirectResponse
# from .main_no_orm import app



# client=TestClient(app)


# def test_endpoints():
#     input_url="https://example.com"
#     post_response=client.post('/shorten',json={"url_link":input_url,"custome_slug":None})
#     response2=client.post('/shorten',json={"url_link":input_url,"custome_slug":None})
#     assert post_response.status_code == 200 
#     post_res=post_response.json()
#     assert post_res is not None
#     print(post_res)
#     short_url=post_res["short_url"]
#     print("short url",short_url)
#     short_code=short_url

#     response2=client.post('/shorten',json={"url_link":input_url,"custome_slug":None})
#     assert response2.status_code == 200
#     res2_short_code=response2.json()["short_url"]
#     assert res2_short_code is not None
#     assert short_code == res2_short_code

#     # short_code="1e1052"
#     # # input_url="https://grafana.com/docs/k6/latest/extensions/"
#     # get_response=client.get(f'/redirect?short_code={short_code}',follow_redirects=False)
#     # assert get_response.status_code == 307
#     # get_res=get_response.headers["Location"]
#     # assert get_res==input_url

    
   
    