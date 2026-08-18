from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connections
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
def health_check(request):
    """Liveness probe: returns 200 if the app is running."""
    logger.info("Liveness probe requested")
    return Response({"status": "ok"})

@api_view(['GET'])
def readiness_check(request):
    """Readiness probe: checks if DB and Redis are reachable."""
    is_ready = True
    services = {"db": "ok", "cache": "ok"}
    
    # Check Database
    try:
        connections['default'].cursor()
    except Exception as e:
        logger.error("Readiness probe DB check failed: %s", str(e))
        services['db'] = "error"
        is_ready = False
        
    # Check Cache (Redis)
    try:
        cache.set('health_check', '1', timeout=1)
    except Exception as e:
        logger.error("Readiness probe Cache check failed: %s", str(e))
        services['cache'] = "error"
        is_ready = False

    status_code = 200 if is_ready else 503
    return Response({"status": "ready" if is_ready else "error", "services": services}, status=status_code)
