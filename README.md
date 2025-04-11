1. Virtual Environment Creation
   We don't want our project dependencies to conflict with general system level dependencies, so let's just build a virtual environment and not contaminate the system environment.

   > python3 -m venv venv (venv python module , virtual environment name)
   > .\venv\Scripts\Activate
   > pip freeze > requirements.txt (to track the installed dependecies into a file requirements with correct versions,so easy to reinstall at once if and when needed later)

   Will use browser as HTTP client or POSTMAN for making http requests requests to server

2) > pip install fastapi
   > pip install "fastapi[standard]"

3) > define path operations/api endpoints/routes to communicate with server via client using aavialable HTTP methods
   > define path handler functions

4) To run the server cd to the folder contaning main.py
   > fastapi dev main.py

To run the loadtest file for checking latency percentiles and also checking success rate of requests - cd to the folder containing loadtest.js in command prompt followed by ->

> K6 run loadtest.js

> Run tests using pytest

Folder structure can be improved further.

Let's observe latency values for api request and response duration from client to server and back to client-->
Code for observing latency values --
https://colab.research.google.com/drive/1qpJnlJ28MZ34DUYDRO8fA0iuxbsHFFxX?usp=sharing


Latency graphs

1. Post requests for already existing url
2. Post requests with new url (for first set of concurrent requests)

![image](https://github.com/user-attachments/assets/995f48df-81bc-4ba2-8be8-82069b327217)

![image](https://github.com/user-attachments/assets/a498ace9-6845-4707-a98e-711e7b306a30)

ValueError: too many file descriptors in select() - Error when requests start getting timed out
> Uvicorn runs a single process by default which cannot handle more than a certain limit of file descriptors at once. Let's increase workers to handle more concurrent requests
> uvicorn backend.main_no_orm:app --host 127.0.0.1 --port 8000 --workers 4
3. Post requests for same url
![image](https://github.com/user-attachments/assets/78bee7df-bb9e-421f-bfdc-2cf336eddef1)
> Now the break point is 1700 concurrent requests.
> If we increase workers it can handle more concurrent requests (it's like 450 requests per worker)

>Even for new request per concurrent user it can handle 1000 concurrent requests as verified using 4 workers(though p values are higher tah nwhen requests are old)

Let's now also observe latency values at various thresholds from which the above latency graphs have been obtained to identify any bottlenecks ,overall performance ,average performance in terms of time duration of request processing and success rate of requests!

For post request 10vus for a duration of 10s
![image](https://github.com/user-attachments/assets/0ea84548-d565-4a3a-89bf-e13d358f6abf)
http_req_duration..............: avg=38.63ms min=7.09ms med=31.81ms max=218.94ms p(50)=31.81ms p(90)=53.48ms p(95)=98.36ms p(99)=195.79ms
{ expected_response:true }...: avg=38.63ms min=7.09ms med=31.81ms max=218.94ms p(50)=31.81ms p(90)=53.48ms p(95)=98.36ms p(99)=195.79ms
http_req_failed................: 0.00% 0 out of 100

We will focus on the http_req_duration for overall performance

1. So on an average request-response total time is 31.81ms (half of requests processed in time less than or equal to ~32 ms)
2. Most requests(90%(90/100) of requests took ~54ms or less,for 80% rise in requests from 50 to 90,processing time increment is ~68% which is okay)
3. 95% requests took ~ 98ms or less (For 5.5% rise in requests from 90 to 95, req. duration increment time is ~8%)
4. 99% requests took ~ 195 ms or less(for further 4.2% rise in requests from 95 to 99, request process time increment is 98% which is huge for only 4 more requests )
5. Last request as total requests 100 took max=218.94ms

For get request
![image](https://github.com/user-attachments/assets/088ab68e-3159-45f6-b15b-06564a7a9c05)

For get request , sleep(0.1s instead of 1s)

![image](https://github.com/user-attachments/assets/b3f6529b-b04f-41e0-9c65-e835a2805e1f)

Test duration 10s --
Assumption 1 req takes minimal amount of time here so ignoring request process times once to find approx per user request frequency .
For a sleep duration of 1s each user can send 1 request per sec .
For a sleep duration of 0.1s each user can send 10 requests per sec .

Put requests

1. 60 concurrent api calls(vus) in stages of 1) ramp up to 10 ,duration -'10s' 2) ramp up to 50 , duration - '10s' 3) ramp up to 60 ,duration '20s' 4) and stay there for '60s' 5) ramp down to 0 in '10s'

![image](https://github.com/user-attachments/assets/a3783664-f6ec-4e3c-adfd-9117af8bf2eb)

2. 100 concurrent api calls(vus) in stages of 1) ramp up to 10 ,duration -'10s' 2) ramp up to 50 , duration - '10s' 3) ramp up to 100 ,duration '40s' 4) ramp down to 0 in '10s'
   ![image](https://github.com/user-attachments/assets/37983e65-9742-40c1-9964-547c7cd216bf)

3)100 vus in 1) { duration: '80s', target: 100 }, 2) ramp down to 0 in 10s
![image](https://github.com/user-attachments/assets/3289edbc-6136-450e-97f2-139e0437bf8e)

While increasing load gradually over a duration of 1 min 20s is sufficient for taking load of 100 concurrent calls, not to conclude anything with this,anyway after some specific time until further duration completion there will 100 concurrent calls for 100 vus.

4.  { duration: '2m', target: 100 },{ duration: '5m', target: 200 },{ duration: '10s', target: 0 }
    ![image](https://github.com/user-attachments/assets/0316ea8e-2315-423b-a7df-fcfa0ef1482b)

requests start getting timed out even for 150 concurrent calls ,
Database is the bottleneck here--
QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00
As there are lots of I/O bound operations so using asynchronosity will help.

After adding async functionality let's see the break point of request time outs --
5){ duration: '3m', target: 100 },{ duration: '12m', target: 150 }, { duration: '10s', target: 0 }
![image](https://github.com/user-attachments/assets/7e42087d-781b-474c-bec8-027ce8c1d610)

6){ duration: '10s', target: 50 },{ duration: '60s', target: 100 }, { duration: '2m', target: 150 },{ duration: '4m', target: 200 },{ duration: '10s', target: 0 }
![image](https://github.com/user-attachments/assets/f815155e-e1fe-48e1-ad69-d556217ad9bb)

Okay let's see how many concurrent calls it can handle for '10s' duration ?

Up to 10 looping VUs for 10s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)
iterations.....................: 54 4.926035/s
![image](https://github.com/user-attachments/assets/cecca4ac-ffc7-4fc1-b871-493ef62ed50c)

Up to 100 looping VUs for 10s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)
iterations.....................: 534 47.991137/s
![image](https://github.com/user-attachments/assets/36a363a9-d4ba-4336-bef0-19e57e7e7fee)

Up to 200 looping VUs for 10s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)
iterations.....................: 922 77.960528/s
![image](https://github.com/user-attachments/assets/5e8fb5d4-5a5c-4a90-9f44-cedef9519cca)

Up to 300 looping VUs for 10s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)
iterations.....................: 1265 107.262163/s
![image](https://github.com/user-attachments/assets/30ec68b4-a771-4e43-aeb7-fe9faee8b4cb)

Up to 400 looping VUs for 10s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)
iterations.....................: 1418 125.314964/s
![image](https://github.com/user-attachments/assets/09bae263-9275-478e-b760-888ed100da03)

When duration is 1s and just increasing concurrent calls
Up to 400 looping VUs for 1s over 1 stages (gracefulRampDown: 30s, gracefulStop: 30s)
running (02.8s), 000/400 VUs, 399 complete and 0 interrupted iterations
![image](https://github.com/user-attachments/assets/62a5dbef-539e-4f47-975e-d9237d87cda8)

So it can only handle around this much of concurrent vus like 460 something until the requests start getting timed out .
Again the database is bottleneck ,like response null errors would occur indicating that api waiting for connection but no available connections found .
Increasing uvicorn workers helped with this (so more concurrent requests can be processed with failures)


Deploy API on Render 
> Create a procfile

> Create api ( New -> Web service -> connect to repo -> specify details -> fill in env variables ( use the internal database url obtained after creating a connection ,add + asyncpg)

> Connect db by creating a new database connection(New -> PostgreSQL -> specify details -> select same region as API service so connection will be faster)

Let's add some analytics for urls as per new requests
>1) Real time analytics for latest 10 urls
>2) Top 10 short urls with most visit counts
   
>As per new requirements let's allow for new unique short codes for same original url too.

>But there is a big issue , if the short urls info is sensitive so there should be some method for user identification so that they don't delete other user's short codes. Let's see few ways to address this.

1)Using API keys in headers
>a) We need to create a users table and link it with url_shortener table using foreign key
>
>b) So we will need schema migrations for this , let's use Alembic
>
>c) pip install alembic
>
>d) alembic init migrations
>
>e) configure alembic.ini file to point to your database
>
>f) use the synchronus driver as psycopg2 because alembic operates in synchronous mode by default
>
>g) sqlalchemy.url = postgresql+psycopg2://username:password@localhost/dbname
>
>h) migrations/env.py find target_metadat variable and point it to SQLAlchemy Base.metadata
>
>i) Generate a migration script-->
>
>j) alembic revision --autogenerate -m "Details for changes"
>
>k) Go to migrations/version ,check if the autogenerated schema changes are as desired. Modify as required.
>
>l) alembic upgrade head to commit the new chnages to database
>
>m) Rollback if necessary using alembic downgrade -1
>
>n) As the table already contains millions of rows so can keep the  user_id column null for earlier enteries or populate it after creating enough users.
>
>o) Use soft deletes for when a short code is requested for deletion.
>
>p) Seeds the users table with few users
>
>q) Run it separately for local environment as a standalone file
>
>r) the file is located inside db folder which is one down from root
>
>s) $env:PYTHONPATH = (Get-Location)
>
>t) $env:PYTHONPATH temporarily sets the PYTHONPATH environment variable to include current root directory path(e.g. url-shortener/) for it's module search, so that if anything imported from up level will not give error, then simply run python db/filename.py

#### Improving concurrency and api response times(OS Ubuntu)
Every api request needs to connect to DB ,total available connections are 5+10 by default in queue pool . So for high concurrency requests start getting timed out as they couldn't get any connections from connection pool of dp api .

Analogy -- Burger menu can take total of 15 requests at a time  for burgers . So until those requests are completed new requests will keep on waiting for their order to be accepted . If no empty slots for new requests until timeout ,new requests will be failed.
with high concurrent requests the pool limit reached because completing requests takes some time and for low concurrency the new requests arrived after some requests got completed so there was space in conn pool for new connections.


> Increasing db connections limit to 20+30 doesn't decrease failure rate by any significant percentage . So we can try to improve API response times .









