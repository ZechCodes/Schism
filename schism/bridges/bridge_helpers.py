import traceback

from schism.bridges.base import ReturnPayload, ExceptionPayload, ResultPayload


class ResponseBuilder:
    """A helper context that captures all exceptions that are raised on the server while attempting to respond to a
    client request.

    In a standard single process application, errors raised by a method are handled by the caller. So it is necessary to
    capture all exceptions raised by a service and propagate them to the client so that the calling code can handle
    those exceptions as normal."""
    def __init__(self):
        self.data: ResultPayload = ReturnPayload(result=None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.data = ExceptionPayload(
                error=exc_val,
                traceback=traceback.format_exception(exc_type, exc_val, exc_tb),
            )

        return True

    def set(self, data):
        """Set the response payload. This payload is overwritten by any exceptions that are raised."""
        self.data = ReturnPayload(result=data)
