class ResponseBuilder:
    """A helper context that captures all exceptions that are raised on the server while attempting to respond to a
    client request.

    In a standard single process application, errors raised by a method are handled by the caller. So it is necessary to
    capture all exceptions raised by a service and propagate them to the client so that the calling code can handle
    those exceptions as normal."""
    def __init__(self):
        self.status = "success"
        self.data = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.status = "error"
            self.data = {
                "error": exc_val,
                "traceback": traceback.format_exception(exc_type, exc_val, exc_tb),
                "context": exc_val.__context__,
                "cause": exc_val.__cause__,
            }

        return True

    def set(self, data):
        """Set the response payload. This payload is overwritten by any exceptions that are raised."""
        self.data = data

    def to_dict(self):
        return {
            "status": self.status,
            "data": self.data,
        }
