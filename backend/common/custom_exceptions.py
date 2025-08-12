
from collections.abc import Callable
from typing import Any, Type, Union
from fastapi import FastAPI, Request,status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse



class UrlShortenerException(Exception):
    """
    Base for all domain errors
      - subclasses *must* define `status_code` and `detail`
    """
    detail: str
    status_code: int

    def __init__(
        self,
        *,
        detail: str | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ):
        # ensure subclass defined defaults
        if status_code is None and getattr(self.__class__, "status_code", None) is None:
            raise TypeError("Subclass of UrlShortenerException must define `status_code`")
        if detail is None and getattr(self.__class__, "detail", None) is None:
            raise TypeError("Subclass of UrlShortenerException must define `detail`")
        
        self.detail = detail if detail is not None else getattr(self, "detail")
        self.status_code = status_code if status_code is not None else getattr(self, "status_code")
        # attach extra context fields (e.g., cart_id, user_id)
        for key, value in kwargs.items():
            setattr(self, key, value)
class BadRequest(UrlShortenerException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Bad request"

class Unauthorized(UrlShortenerException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required or invalid credentials"

class Forbidden(UrlShortenerException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Forbidden"

class NotFound(UrlShortenerException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Short code not found or deleted"

class CustomSlugConflict(UrlShortenerException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Custom slug already exists; choose another."

class ShortCodeCollision(UrlShortenerException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Short code collision; please retry or choose custom slug"

class CodeGone(UrlShortenerException):
    status_code = status.HTTP_410_GONE
    detail = "Short code expired"

class UpdateFailed(UrlShortenerException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Could not update short code"

class DBUnavailable(UrlShortenerException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Database unavailable; try again later"

class CacheError(UrlShortenerException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Cache unavailable"

class InternalServerError(UrlShortenerException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error"


# detail_fn can be allowed to accept any Exception as well 
DetailFn = Callable[[UrlShortenerException], Any]

def create_exception_handler(detail_fn:DetailFn):
    async def exception_handler(request:Request, exc:UrlShortenerException):   
        # if not isinstance(exc, UrlShortenerException):
        #     # (should never happen in per‑type registrations)
        #     return JSONResponse(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         content={"message": "Internal server error", "error_type": type(exc).__name__},
        #     ) 
        try:
            body = detail_fn(exc)     
            code = exc.status_code
        except Exception as e:
            # Something *went wrong in handler code itself*—
            # e.g. `` was missing and got an AttributeError.
            body = {"detail": str(e)}
            code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        return JSONResponse(status_code=code, content=body)
      
    return exception_handler

# use a different handler for unhandled exceptions as detail_fn is denfined for UrlShortenerException subclasses
async def fallback_handler(request: Request, exc: Exception):
    
    body = {
        "detail": getattr(exc, "detail", "nternal Server Error"),
        "error_type": type(exc).__name__
    }
    code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    print("falback exception")
    return JSONResponse(status_code=code, content=body)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    #* log in logger
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation failed",
            "detail": exc.errors(),
        },
    )

def register_exceptions(app: FastAPI):

    mapping : list [tuple[Type[UrlShortenerException],DetailFn]]=[
        (BadRequest, lambda exc: {"detail": exc.detail})
           
    ]

    # for exc_cls, fn in mapping:
    #     app.add_exception_handler(
    #         exc_cls,
    #         create_exception_handler(detail_fn=fn)
    #     )

    app.add_exception_handler(
        Exception, # catch all unidentified/unhandled exceptions
        fallback_handler
    )

    app.add_exception_handler(
        RequestValidationError, # catch all unidentified/unhandled exceptions
        validation_exception_handler
    )
