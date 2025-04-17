import asyncio , time, httpx,os,statistics
from dotenv import load_dotenv

load_dotenv()
valid_api_key=os.getenv("valid_api_test_key")
valid_api_key2=os.getenv("valid_api_key_2")
valid_api_key3=os.getenv("valid_api_key_3")
invalid_key="invalid_key"


BASE_URL="http://127.0.0.1:8000"
valid_code="something"
code_to_del=""
post_url_payload="https://www.youtube.com/watch?v=mHfn_7ym6to&list=PLl8XY7QVSa4aUyZAtL2Hlf_mx3LaSix9B&index=9"
no_slug_link="https://leetcode.com/studyplan/top-interview-150/"
new_post="https://self-chz.sentry.io/profiling/?project=4509156804919296&statsPeriod=14d"

endpoints = {
    "redirect": {
        "method": "GET",
        "url": f"{BASE_URL}/redirect?short_code={valid_code}",
        "headers": {},  # No API key header for redirect
    },
    "user_urls": {
        "method": "GET",
        "url": f"{BASE_URL}/user/urls",
        "headers": {"api-key": valid_api_key},
    },
    "shorten_post": {
        "method": "POST",
        "url": f"{BASE_URL}/shorten",
        "headers": {"api-key": valid_api_key2},
        "json": {
            "url_link": new_post,
            "custom_slug": "prifile",
            "exp_date": None
        },
    },
    "shorten_noslug": {
        "method": "POST",
        "url": f"{BASE_URL}/shorten",
        "headers": {"api-key": valid_api_key2},
        "json": {
            "url_link": no_slug_link,
            "exp_date": None
        },
    },
    "update": {
        "method": "PATCH",
        "url": f"{BASE_URL}/shorten/fpimidware?expiry_date=2025-03-12",
        "headers": {"api-key": valid_api_key2},
    },
}


def stats_calc(res_times,endpoint,iterations):
    avg_time=sum(res_times)/len(res_times)
    min_time = min(res_times)
    max_time = max(res_times)
    median_time = statistics.median(res_times)
    p90 = statistics.quantiles(res_times, n=100)[89]  # 90th percentile approximation

    print(f"\nBenchmark Results for {endpoint}:")
    print(f"Requests run: {iterations}")
    print(f"Average response time: {avg_time:.4f} seconds")
    print(f"Median response time: {median_time:.4f} seconds")
    print(f"Minimum response time: {min_time:.4f} seconds")
    print(f"Maximum response time: {max_time:.4f} seconds")
    print(f"90th percentile response time: {p90:.4f} seconds\n")


async def benchmark(full_endpoint:dict,iterations:int=100,warmup:int=5):
    url=full_endpoint["url"]
    method=full_endpoint.get("method","GET")
    headers=full_endpoint.get("headers",{})
    payload=full_endpoint.get("json",None)

    async with httpx.AsyncClient() as client:
        for _ in range(warmup):
            if method.upper=="GET":
                await client.get(url,headers=headers,follow_redirects=False)
            elif method.upper=="POST":
                await client.post(url,headers=headers,json=payload)
            elif method.upper=="PATCH":
                await client.post(url,headers=headers)

        res_times=[]
        for i in range(iterations):
            start_time=time.perf_counter()
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, follow_redirects=False)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=payload)
            elif method.upper=="PATCH":
                response=await client.post(url,headers=headers)
            end_time=time.perf_counter()
            process_time=end_time-start_time
            res_times.append(process_time)
            # print(f"Iteration {i+1}: {process_time:.4f} s")
        
    stats_calc(res_times,url,iterations)
    


async def main():

    for key,endpoint in endpoints.items():
        print(f"{key}:{endpoint['url']}")
    
    choice=input("Enter the endpoint key to benchmark: ").strip()
    if choice not in endpoints:
        print(f"Endpoint '{choice}' not found. Please try with valid key present before :")

    endpoint_to_test = endpoints[choice]
    
    print(f"Benchmarking endpoint '{choice}' with URL: {endpoint_to_test['url']}")
    await benchmark(endpoint_to_test,iterations=100)

if __name__ == "__main__":
    asyncio.run(main())


"""
Benchmark Results for http://127.0.0.1:8000/shorten:
Requests run: 100
Average response time: 0.0166 seconds
Median response time: 0.0116 seconds
Minimum response time: 0.0103 seconds
Maximum response time: 0.4050 seconds
90th percentile response time: 0.0143 seconds
"""
# get endpoint average response time
# without update 9ms
# with update 31 ms 

# Requests run: 500

# full read and normal update 
# Average response time: 0.0387 seconds
# Median response time: 0.0282 seconds
# Minimum response time: 0.0172 seconds
# Maximum response time: 0.3751 seconds
# 90th percentile response time: 0.0415 seconds

# reqd read and normal update 
# Average response time: 0.0351 seconds
# Median response time: 0.0279 seconds
# Minimum response time: 0.0159 seconds
# Maximum response time: 0.3328 seconds
# 90th percentile response time: 0.0395 seconds

# ORM full load and required fields load almost very same and kinda inconclusive 
# Average response time: 0.0303 seconds
# Median response time: 0.0275 seconds
# Minimum response time: 0.0158 seconds
# Maximum response time: 0.3501 seconds
# 90th percentile response time: 0.0380 seconds

# Benchmark Results for http://127.0.0.1:8000/shorten:
# Requests run: 500
# Average response time: 0.0668 seconds
# Median response time: 0.0578 seconds
# Minimum response time: 0.0186 seconds
# Maximum response time: 0.3193 seconds
# 90th percentile response time: 0.0861 seconds

# Benchmark Results for http://127.0.0.1:8000/redirect?short_code=something:
# Requests run: 500
# Average response time: 0.0547 seconds
# Median response time: 0.0314 seconds
# Minimum response time: 0.0246 seconds
# Maximum response time: 0.4079 seconds
# 90th percentile response time: 0.0818 seconds




