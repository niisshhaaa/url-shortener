# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- (future new features go here)

### Changed
- (future backwards‑compatible enhancements)

### Fixed
- (future bug fixes)

---

## [1.0.0] – 2025‑07‑26

### Added
- **Core URL shortening**:  
  - `POST /shorten` generates a unique short code for any valid HTTP/HTTPS URL  
  - Custom slugs/short_code and server generated short_code slugs .   
  - Optional expiration date (`exp_date`) in `YYYY‑MM‑DD` format  
  - Optional password protection on a per‑URL basis  
- **Batch shortening**:  
  - `POST /shorten/batch` accepts an array of URLs, returns per‑item successes and failures  
  - Schema‑level and domain‑level validation with partial‑success and partial-failure reporting  
- **Update endpoints**:  
  - `PATCH /shorten/{short_code}` to modify `expiry_date` and/or password (with authentication and current‑password check) 
  - Codes can be deactivated and reactivated by expiry_date
- **Get endpoints**:
  - `GET /redirect` to get urls associated with short codes , requires password for password protected codes.
- **Delete endpoints**:   
  - Supports Soft‑deletes
- **Analytics & listing**:  
  - `GET /analytics/latest` returns the last N shortened URLs (paginated, ordered by creation time)  
  - `GET /urls` (or `/urls`) lists all URLs owned by the authenticated user, with pagination  
- **Infrastructure & tooling**:  
  - Database migrations via Alembic, including current indexes for url_shoretenr on `created_at` and partial unique index on `(short_code) WHERE deleted_at IS NULL`,composite index on `visit_cnt, last_accessed_at` , `user_id` index , `id` pkey index . 
  - Input validation + Pydantic (strict `HttpUrl`, `date` fields, custom validators)  
  - Asynchronous processing with SQLAlchemy AsyncSession and optional batch concurrency via `asyncio.gather`

### Security
- Authentication middleware enforces per‑user identification on every endpoint.
- Authorization middleware enforces further fine grained scope on the basis of user roles.
- All sensitive data (passwords) are accepted in **request bodies**, not query parameters.  
