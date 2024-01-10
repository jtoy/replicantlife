from http.server import SimpleHTTPRequestHandler, HTTPServer
from itertools import cycle

# List of backend servers to balance requests
backend_servers = [
    ('localhost', 8001),
    ('localhost', 8002),
    ('localhost', 8003),
]

class RoundRobinProxyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend_iterator = cycle(backend_servers)

    def get_next_backend(self):
        return next(self.backend_iterator)

    def do_GET(self):
        backend_host, backend_port = self.get_next_backend()

        self.log_message("Proxying request to backend server: %s:%s" % (backend_host, backend_port))

        self.headers['Host'] = '%s:%s' % (backend_host, backend_port)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Forward the request to the selected backend server
        self.proxy_request(backend_host, backend_port)

    def proxy_request(self, host, port):
        with self.send_to_backend(host, port) as backend:
            data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            backend.sendall(data)

            response = self.get_response_from_backend(backend)
            self.wfile.write(response)

    def send_to_backend(self, host, port):
        backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend.connect((host, port))
        return backend

    def get_response_from_backend(self, backend):
        response = b""
        while True:
            data = backend.recv(4096)
            if not data:
                break
            response += data
        return response

if __name__ == '__main__':
    try:
        server_address = ('localhost', 8888)
        httpd = HTTPServer(server_address, RoundRobinProxyHandler)
        print('Round-robin proxy server started on {}:{}'.format(*server_address))
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Proxy server stopped.')

