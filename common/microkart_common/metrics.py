from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter("http_requests_total", "HTTP requests", ["service", "method", "route", "status"])
HTTP_LATENCY = Histogram("http_request_duration_seconds", "HTTP latency", ["service", "route"])
EVENTS_PUBLISHED = Counter("events_published_total", "Events relayed from outbox", ["service", "topic", "type"])
EVENTS_CONSUMED = Counter("events_consumed_total", "Events consumed", ["service", "topic", "type", "result"])
