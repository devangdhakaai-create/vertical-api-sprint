import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

log = structlog.get_logger()

#TimeStamper = har log entry mein timestamp add karega
#JSONRenderer = logs ko JSON format mein print karega (production mein easy parsing ke liye — log aggregation tools jaise ELK/Datadog JSON logs prefer karte hain)