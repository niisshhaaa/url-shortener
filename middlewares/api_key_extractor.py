from fastapi import Request, HTTPException, status

async def extract_api_key_from_authorization_header(request: Request) -> str:
    """
    Extracts the API key from the Authorization header in the format 'Bearer <api_key>'.
    Raises HTTPException if the header is missing or malformed.
    Returns the API key string if valid.
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected format: 'Bearer <api_key>'",
        )
    api_key = auth_header[7:].strip()  # Remove 'Bearer ' (case-insensitive)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing in Authorization header.",
        )
    return api_key 