# def greet(userFav,name="orange", latsname="user",age=28):
#     print(f"Hello {name} {latsname}, you are {age} years old! something you love most is {userFav}")

# greet(latsname="nisha",userFav="Free Running")
# greet("Free Running ","blue","nisha")

# from fastapi import HTTPException
# def check_res_of_error(num=10):
#     if(num==10):
#         return 10
#     raise HTTPException(status_code=400,detail="only 10 allowed")

# error_res=check_res_of_error(11)
# print(error_res)


# endpoints = {
#     "redirect": {
#         "method": "GET",
#         "headers": {},  # No API key header for redirect
#     },
#     "user_urls": {
#         "method": "GET",
#     },
#     "shorten_post": {
#         "method": "POST",
#         "headers": {"api-key": ""},
#         "json": {
#             "url_link": "",
#             "custom_slug": "undiscreterv",
#             "exp_date": None
#         },
#     },
#     "update": {
#         "method": "PATCH",
#         "headers": {"api-key": ""},
#     },
# }

# for key,endpoint in endpoints.items():
#     print(f"{key}:{endpoint['url']}")
    
# choice=input("Enter the endpoint key to benchmark: ").strip()
# if choice not in endpoints:
#     print(f"Endpoint '{choice}' not found. Please try with valid options")

# endpoint_to_test = endpoints[choice]
    
# print(f"Benchmarking endpoint '{choice}' with URL: {endpoint_to_test['url']}")