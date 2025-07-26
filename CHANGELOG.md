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

## [1.0.0] – 2025‑15-01
### Added
- **Core URL shortening**:  
  - `POST /shorten` generates a unique short code for any valid HTTP/HTTPS URL  
  - Server generated short_code slugs . 
- **Get endpoints**:
  - `GET /redirect` to get urls associated with short codes 
- **Delete endpoints**:   
  - Supports Soft‑deletes
- **Infrastructure & tooling**:  
  - Database migrations via Alembic
 
