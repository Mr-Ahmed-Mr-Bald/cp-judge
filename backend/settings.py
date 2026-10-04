# The worker opens its own dedicated connection to LISTEN on, using
# psycopg2 directly (worker._open_listener). It deliberately bypasses
# SQLAlchemy: the raw driver APIs it needs -- set_isolation_level,
# poll, fileno -- are psycopg2's, and going through the ORM would hand
# back whichever driver the postgresql:// URL happens to resolve to
# (SQLAlchemy 2.1 defaults that scheme to psycopg, which does not have
# the same API).
LISTEN_CHANNEL = "new_submission"
# Fallback poll, not the normal path: a notification normally wakes the
# worker at once. This only bounds how long a missed notification goes
# unnoticed.
LISTEN_TIMEOUT = 20.0