# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

* (future backwards‑compatible new features)


### Changed

* (future backwards‑compatible enhancements)


### Fixed

* (future bug fixes)

---

## [2.1.0] – 2025‑08‑06

- Redis-backed caching for `/redirect` endpoint (cache-aside with per-key locks to prevent db thundering-herd, TTL configurable).  
- `/cache-stats` endpoint exposing cache hits, misses, and hit-ratio. It doesn't persist server restarts.
- IP- and API-key-based(Protected endpoints) rate-limiting middleware:
  - Default: 50 req/min per IP
  - Per-route limits (`/shorten`: 10 req/s, `/redirect`: 50 req/s)
  - “Free” tier override: 5 req/min for free-tier users  

----

## [2.0.0] – 2025‑07‑26

### Added

* **Authentication layer**:

  * Mandatory `Authorization: Bearer <token>` header on all endpoints
  * Authentication middleware enforces per‑user identification on every endpoint.
  * Authorization middleware enforces further fine grained scope on the basis of user roles.

* **Batch shortening**:  
  * `POST /shorten/batch` accepts an array of URLs, returns per‑item successes and failures  
  * Schema‑level and domain‑level validation with partial‑success and partial-failure reporting  

* **Custom slugs & password updates**:
  * Added support for custom slugs
  * Modified shorten POST payload to include slug ,password and expiry date fields
  * Codes can be deactivated and reactivated by expiry_date in update endpoint .

* **Analytics & listing**:  
  - `GET /latest-urls` returns the last N shortened URLs (paginated, ordered by creation time)  
  - `GET /urls` lists all URLs owned by the authenticated user, with pagination  

* **Infrastructure & tooling**:
* Input validation + Pydantic (strict `HttpUrl`, `date` fields, custom validators)  
* Asynchronous processing with SQLAlchemy AsyncSession and optional batch concurrency via `asyncio.gather`


### Changed
* `GET /shorten/{code}` now accepts an optional `password` query parameter.
   - If the stored URL is password‑protected, returns **401 Unauthorized** instead of redirect.

### Security

* Authentication & Authorization middlewares enforce per‑user and role‑based access controls

### Deprecated
* Unauthenticated access to [`/shorten`, `/shorten/batch`, `/redirect`, `/urls`] will be **removed in next major release** (target date: 2025‑09‑30). Clients **must** start sending Bearer API key in `Authorization` header now.

---

## [1.0.0] – 2025‑01‑15

### Added
* **Core URL shortening**:  
  * POST /shorten generates a unique short code for any valid HTTP/HTTPS URL  
  * Server generated short_code slugs . 
* **Get endpoints**:
  * GET /redirect to get urls associated with short codes 
* **Delete endpoints**:   
  * Supports Soft‑deletes

* **Infrastructure & tooling**:  
  * Database migrations via Alembic, including current indexes for url_shoretenr on `created_at` and partial unique index on `(short_code) WHERE deleted_at IS NULL`,composite index on `visit_cnt, last_accessed_at` , `user_id` index , `id` pkey index . 
  
---

*This changelog follows Semantic Versioning and Keep a Changelog guidelines.*

 
