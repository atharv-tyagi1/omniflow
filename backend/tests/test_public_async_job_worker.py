import pytest
from backend.app.services.public.async_job_worker import PublicAsyncJobWorker
from backend.app.core.public_errors import PublicAPIException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

def test_is_transient_error():
    # Transient ones
    assert PublicAsyncJobWorker._is_transient_error(PublicAPIException("Rate Limit", status_code=429)) is True
    assert PublicAsyncJobWorker._is_transient_error(PublicAPIException("Bad Gateway", status_code=502)) is True
    assert PublicAsyncJobWorker._is_transient_error(Exception("Random generic exception")) is True
    
    # Permanent ones
    assert PublicAsyncJobWorker._is_transient_error(PublicAPIException("Bad Request", status_code=400)) is False
    assert PublicAsyncJobWorker._is_transient_error(PublicAPIException("Unauthorized", status_code=401)) is False
    assert PublicAsyncJobWorker._is_transient_error(PublicAPIException("Forbidden", status_code=403)) is False
    assert PublicAsyncJobWorker._is_transient_error(RequestValidationError([])) is False
    assert PublicAsyncJobWorker._is_transient_error(IntegrityError("stmt", "params", "orig")) is False
