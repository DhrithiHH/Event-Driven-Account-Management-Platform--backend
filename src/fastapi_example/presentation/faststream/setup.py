import faststream.__about__
from dishka import AsyncContainer
from faststream import FastStream
from faststream.kafka import KafkaBroker

# Compatibility shim: dishka 1.x validates against FastStream 0.6.x.
# If FastStream 0.7+ is installed in any environment, temporarily spoof the version for import.
if not faststream.__about__.__version__.startswith(("0.5", "0.6")):
    _orig_ver = faststream.__about__.__version__
    faststream.__about__.__version__ = "0.6.15"
    try:
        from dishka.integrations.faststream import setup_dishka
    finally:
        faststream.__about__.__version__ = _orig_ver
else:
    from dishka.integrations.faststream import setup_dishka

from .consumers import email_notifications_router, setup_routers


async def init_faststream(di_container: AsyncContainer) -> FastStream:
    broker = await di_container.get(KafkaBroker)
    setup_routers(broker, email_notifications_router)
    app = FastStream(broker)
    setup_dishka(di_container, app, auto_inject=True)
    return app
