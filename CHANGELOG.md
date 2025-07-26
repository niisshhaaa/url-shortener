# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

* (future new features go here)

### Changed

* (future backwards‑compatible enhancements)

### Fixed

* (future bug fixes)

---

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
  * `PATCH /shorten/{short_code}` enhanced to require `current_password` for protected codes and accept `new_password` in body
  * Codes can be deactivated and reactivated by expiry_date in update endpoint .
  * Get endpoints requires password for password protected codes .

* **Analytics & listing**:  
  - `GET /analytics/latest` returns the last N shortened URLs (paginated, ordered by creation time)  
  - `GET /urls` (or `/urls`) lists all URLs owned by the authenticated user, with pagination  

* **Infrastructure & tooling**:
* Input validation + Pydantic (strict `HttpUrl`, `date` fields, custom validators)  
* Asynchronous processing with SQLAlchemy AsyncSession and optional batch concurrency via `asyncio.gather`


### Changed

* Soft‑delete now enforced by partial unique index on `(short_code) WHERE deleted_at IS NULL`
* All sensitive data moved to request bodies; removed any query‑param password/API‑key usage

### Security

* Authentication & Authorization middlewares enforce per‑user and role‑based access controls
* Deprecated v1 endpoints generate `Warning: 299` headers until removal on 2025‑09‑01

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
  

### Deprecated

* Unscoped listing endpoints without Authentication

---

*This changelog follows Semantic Versioning and Keep a Changelog guidelines.*

 
