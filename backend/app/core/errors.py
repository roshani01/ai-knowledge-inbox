from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.app.core.logging import logger


HTTP_422 = 422


class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SSRFSecurityError(AppException):
    def __init__(self, message: str = "Invalid or restricted URL target."):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class UrlFetchError(AppException):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=HTTP_422)


class EmbeddingServiceError(AppException):
    def __init__(self, message: str = "Embedding generation failed."):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)


class LLMServiceError(AppException):
    def __init__(self, message: str = "Language model service error."):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)


class ItemNotFoundError(AppException):
    def __init__(self, item_id: str):
        super().__init__(message=f"Knowledge item '{item_id}' not found.", status_code=status.HTTP_404_NOT_FOUND)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning("Application exception at %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_type": exc.__class__.__name__},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        clean_errors = []
        error_messages = []
        for err in exc.errors():
            loc = " -> ".join(str(p) for p in err.get("loc", []))
            msg = str(err.get("msg", "Invalid value"))
            error_messages.append(f"{loc}: {msg}" if loc else msg)
            clean_errors.append({
                "loc": [str(p) for p in err.get("loc", [])],
                "msg": msg,
                "type": str(err.get("type", "")),
            })
        summary = "; ".join(error_messages)
        logger.info("Validation error at %s: %s", request.url.path, summary)
        return JSONResponse(
            status_code=HTTP_422,
            content={"detail": summary, "errors": clean_errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled server exception at %s: %s", request.url.path, str(exc), exc_info=False)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please try again later."},
        )
