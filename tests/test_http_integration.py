from __future__ import annotations

import json
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from gxp.edge import EdgeAgent, SQLiteEdgeSpool
from gxp.ingestion import IngestionStore
from gxp.server import GXPHTTPServer, GXPRequestHandler
from gxp.transports.http import HttpTransport

from helpers import make_position


class HttpIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.store = IngestionStore(f"{self.temporary_directory.name}/server.db")
        self.token = self.store.bootstrap_device("busroot-kerala", "bus-104-gps")
        self.server = GXPHTTPServer(("127.0.0.1", 0), GXPRequestHandler, self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        port = self.server.server_address[1]
        self.endpoint = f"http://127.0.0.1:{port}/v1/events"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary_directory.cleanup()

    def test_authenticated_edge_flush_is_acknowledged(self) -> None:
        spool = SQLiteEdgeSpool(f"{self.temporary_directory.name}/edge.db")
        agent = EdgeAgent("busroot-kerala", "bus-104-gps", spool, clock_quality="gnss")
        make_position(agent)
        result = agent.flush(HttpTransport(self.endpoint, self.token))
        self.assertEqual(result, {"acknowledged": 1, "retried": 0, "rejected": 0})
        self.assertEqual(self.store.event_count(), 1)

    def test_unauthenticated_post_is_rejected(self) -> None:
        request = Request(
            self.endpoint,
            data=json.dumps({}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as context:
            urlopen(request)
        self.assertEqual(context.exception.code, 401)

