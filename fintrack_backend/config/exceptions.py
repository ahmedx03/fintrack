"""
Custom DRF exception handler.

In production, unhandled server errors return a generic JSON message
instead of a stack trace. All errors are logged server-side.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # Let DRF handle known API exceptions (400, 401, 403, 404, etc.)
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # Unhandled exception — log it fully, return nothing useful to the client
    view = context.get('view', '')
    logger.error(
        'Unhandled server error in %s: %s',
        view.__class__.__name__ if view else 'unknown',
        exc,
        exc_info=True,
    )
    return Response(
        {'detail': 'A server error occurred. Please try again later.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
