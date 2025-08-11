1. Virtual Environment Creation
   > We don't want our project dependencies to conflict with general system level dependencies, so let's just build a virtual environment and not contaminate the system environment.

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


Let's observe latency values for api request and response duration from client to server and back to client-->

<img width="1840" height="884" alt="image" src="https://github.com/user-attachments/assets/14071fa6-d90b-409c-bff5-17d13774ca0b" />
For shorten requests approx 2000 vus with 60 req/s can be handled without any db connect timeouts where all requests reach to succession.
<img width="1840" height="884" alt="image" src="https://github.com/user-attachments/assets/6d1b9cad-e37f-44f3-b913-9aef0011edb0" />
For get requests approx 980 vus with 30 req/s .

#### Improving concurrency and api response times
Every api request needs to connect to DB ,total available connections are 5+10 by default in queue pool . So for high concurrency requests start getting timed out as they couldn't get any connections from connection pool of dp api .

Analogy -- Burger menu can take total of 15 requests at a time  for burgers . So until those requests are completed new requests will keep on waiting for their order to be accepted . If no empty slots for new requests until timeout ,new requests will be failed.
with high concurrent requests the pool limit reached because completing requests takes some time and for low concurrency the new requests arrived after some requests got completed so there was space in conn pool for new connections.

> Increasing db connections limit to 20+30 doesn't decrease failure rate by any significant percentage . So we can try to improve API response times even further .


### Caching (redirect endpoint)
> Cache-aside using Redis: url:{short_code} → cached payload.

> Distributed per-key lock when populating or overwriting the cache to avoid thundering-herd across multiple workers/processes.

> Fallback: per-process asyncio.Lock if Redis is unavailable.

> Writes are retried in background if Redis is temporarily unreachable.

> Cache TTL configurable per key.

> Observed impact (k6): mean latency reduced from ~882 ms (no cache) to ~563 ms (cache + locking) → ~**319 ms average improvement per request; median and p95 also improved (median ≈ 268 ms improvement, p95 ≈ 1.1 s improvement**).

> Earlier, without robust locking/stats writes, ~1 s improvement observed ; adding cross-process correctness (locks, stats writes, retries) reduced raw gain but made the system safe for multi-worker deployments.

Note: We intentionally do not perform per-hit Redis counter increments on the hot path in production — collect metrics via Prometheus client or batch writes instead to avoid extra round-trips.

> Option for lower latency (experiment)
Can avoid distributed locks for writes using a Lua CAS pattern: store an updated_at (or monotonic version) in both DB and cache, and use a tiny Lua script (EVAL) that atomically writes only if new_version >= existing_version. This is server-side atomic and reduces round trips. Recommended experiment if you want to trade added implementation work for somewhat lower latency.


Deploy API on Render 
> Create a procfile

> Create api ( New -> Web service -> connect to repo -> specify details -> fill in env variables ( use the internal database url obtained after creating a connection ,add + asyncpg)

> Connect db by creating a new database connection(New -> PostgreSQL -> specify details -> select same region as API service so connection will be faster)

> To create schema(tables,relations,contraints...) and autodeploy schema migrations with alembic update start command to -- alembic upgrade head && gunicorn -k uvicorn.workers.UvicornWorker src:app

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


#### Prometheus + Grafana Monitoring + Sentry Error tracking and Profiling

![Screenshot from 2025-04-17 15-48-49](https://github.com/user-attachments/assets/c9b0d094-dcc3-4a65-bb3a-ebffbdf1ba3e)
> the lowest graph curves are for average response times(mean/average latency over 5 min window)

> 3 horizontal deviations for diffrent latency like p50 ,p90 and p99. For shorten 200 requests sent with some time gap for with slug case and the spike in shorten is like for next 100 it was called without slug(with more checks)


















