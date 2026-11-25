import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from gui import Handler


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def request(self, path, payload=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        conn.request('GET' if payload is None else 'POST', path, payload,
                     headers or ({'Content-Type': 'application/json'} if payload else {}))
        response = conn.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        conn.close()
        return result

    def test_assets(self):
        for path in ('/', '/app.js', '/app.css'):
            status, body, headers = self.request(path)
            self.assertEqual(status, 200)
            self.assertGreater(len(body), 100)
            self.assertIn("script-src 'self'", headers['Content-Security-Policy'])

    def test_examples(self):
        status, body, _ = self.request('/api/examples')
        self.assertEqual(status, 200)
        self.assertTrue(any(e['name'] == '08_tipos_e_escopos' for e in json.loads(body)))

    def test_run_and_isolation(self):
        source = 'estacionamento T { vaga A1 comum entrada "ABC1234" estacionar "ABC1234" em A1 }'
        _, body, _ = self.request('/api/run', json.dumps({'source': source}))
        self.assertEqual(json.loads(body)['state']['occupied'], {'A1': 'ABC1234'})
        _, body, _ = self.request('/api/run', json.dumps({'source': 'estacionamento T { vaga A2 pcd }'}))
        self.assertEqual(json.loads(body)['state']['spaces'], {'A2': 'pcd'})

    def test_type_error_partial_state(self):
        _, body, _ = self.request('/api/run', json.dumps({'source': 'estacionamento T { vaga A1 comum entrada A1 }'}))
        result = json.loads(body)
        self.assertEqual(result['error']['code'], 'T001')
        self.assertEqual(result['accepted_commands'], 1)

    def test_invalid_json(self):
        self.assertEqual(self.request('/api/run', '{')[0], 400)

    def test_missing_source(self):
        self.assertEqual(self.request('/api/run', '{}')[0], 400)

    def test_cross_origin(self):
        self.assertEqual(self.request('/api/run', '{}', {'Content-Type': 'application/json', 'Origin': 'https://example.com'})[0], 403)

    def test_unknown_path(self):
        self.assertEqual(self.request('/../gui.py')[0], 404)

    def test_wrong_content_type(self):
        self.assertEqual(self.request('/api/run', '{}', {'Content-Type':'text/plain'})[0], 415)

    def test_limit(self):
        self.assertEqual(self.request('/api/run', json.dumps({'source':' ' * 65537}))[0], 400)
