"""AWS Lambda entry — Mangum ASGI adapter.

Set ``LAMBDA_APP_MODULE`` to ``api.main`` for full agent (Unit 7), or default spike app.
"""

from __future__ import annotations

import importlib
import os

from mangum import Mangum

_module = os.environ.get("LAMBDA_APP_MODULE", "api.lambda_spike")
_app = importlib.import_module(_module).app

handler = Mangum(_app, lifespan="off")
