from qdrant_client import QdrantClient

from .settings import Settings


def get_qdrant_client(settings: Settings):
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
