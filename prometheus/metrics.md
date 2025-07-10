## API Performance & Resource Metrics Reference

This document lists key Prometheus queries (PromQL) for monitoring API performance, resource usage, errors, and latency. Each section explains what the query calculates, how it works, and what insights it provides.

---

### 1. CPU Utilization (%)

```promql
100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

**What does `avg by(instance)` mean?**

* Prometheus collects `node_cpu_seconds_total` per CPU core. `rate(...[5m])` gives the per-second idle seconds for each core over past [5m] window.
* `avg by(instance)(...)` averages the idle rate across all cores in each host instance, producing a single idle percentage per machine.

**Why use this?**

* Correlate host CPU saturation with spikes in API latency or error rates.

---

### 2. Memory Utilization (%)

```promql
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
  / node_memory_MemTotal_bytes * 100
```

**What does this calculate?**

* `node_memory_MemTotal_bytes`: total RAM on the host.
* `node_memory_MemAvailable_bytes`: free RAM available for applications.

**Why use this?**

* Detect system memory pressure that can lead to OOM kills or swap thrashing under load.

---

### 3. Server Error Rate (%)

```promql
sum(rate(http_requests_total{status_code=~"5.."}[1m]))  
/ sum(rate(http_requests_total[1m])) * 100
```

**What does this show?**

* Numerator: per-second rate of 5xx responses (server errors).
* Denominator: total request rate.
**percentage of requests failing with 5xx**

**Why use this?**

* Track degradation in service quality; alerts if error rate exceeds thresholds.

---

### 4. Application Resident Memory (RSS)

```promql
process_resident_memory_bytes{job="url_shorts"}
```

**What is this?**

* The Resident Set Size (RSS) of the FastAPI process: physical RAM usage in bytes.

**Why use this?**

* Monitor for memory leaks; ensure process memory stays within expected bounds.

---

### 5. Disk Space Available (bytes)

```promql
node_filesystem_avail_bytes{mountpoint="/", fstype!~"tmpfs|overlay"}
```

**What does this measure?**

* Free bytes on the root filesystem, excluding in-memory (`tmpfs`) and overlay filesystems.

**Why use this?**

* Prevent log or temp file growth from filling disk and causing application failures.

---

### 6. Open File Descriptors

```promql
process_open_fds{job="url_shorts"}
```

**What is this?**

* Number of file descriptors (files, sockets) open by the FastAPI process.

**Why use this?**

* Detect approaching system limits (EMFILE errors) which block new connections or file operations.

---

### 7. In‑Flight Requests per Endpoint

```promql
sum(inprogress_requests) by (handler)
```

*(Use `handler` or `path_template` depending on your instrumentation.)*

**What does this show?**

* Number of concurrent requests currently being processed per route template.

**Why use this?**

* Identify endpoints that are saturated and causing increased latency or queueing.

---

### 8. Database Connection Pool Usage (%)

```promql
db_connection_pool_used{job="url_shorts"}
  / db_connection_pool_max{job="url_shorts"} * 100
```

**What does this calculate?**

* Fraction of your SQLAlchemy pool in use.

**Why use this?**

* Spot pool exhaustion causing connection wait times or timeouts under load.

---

### 9. Database Query p95 Latency (seconds)

```promql
histogram_quantile(0.95,
  sum(rate(db_query_duration_seconds_bucket{job="url_shorts"}[5m]))
    by (le)
)
```

**What does this compute?**

* 95th percentile of DB query durations over 5 minutes.

**Why use this?**

* Detect slow queries (missing indexes, N+1 patterns) impacting end-to-end latency.

---

### 10. API Latency Percentiles per Endpoint

```promql
histogram_quantile(0.99,
  sum by (le, handler)(
    rate(http_request_duration_seconds_bucket{handler!="/metrics"}[5m])
  )
)
```


**What does this calculate?**

* 99th percentile request latency per route template.

**Why use this?**

* Monitor tail latency and set SLOs for user experience.

---

## Summary of Insights

* **CPU & Memory** metrics correlate resource pressure with latency spikes.
* **Error rates** highlight service degradation and guide alert thresholds.
* **Process memory and FDs** guard against resource leaks that cause service instability.
* **In‑flight requests** and **DB pool usage** pinpoint concurrency bottlenecks.
* **Latency percentiles** (p50/p95/p99) quantify user‑perceived performance and SLO compliance.

Use these queries in your Grafana panels (code mode) and organize them into rows for a clear, at‑a‑glance health dashboard.


Percentile Calculation ----

1) le buckets -- requests with latency less than equal to a particular le will count up in that bucket and in higher le buckets.
2) Calculate rate over some time window .
3) Sum by (handler,le)
4) To calculate 90th percentile do 90%(total requests).Locate where it lies on le line .


