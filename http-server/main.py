import os
import socket
import mimetypes
import shutil


class TCPServer:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)

        print("Listening at", s.getsockname())

        while True:
            conn, addr = s.accept()

            print("Connected by", addr)

            data = conn.recv(1024)
            response = self.handle_request(data)
            conn.sendall(response)

            conn.close()

    def handle_request(self, data):
        return data


class HTTPServer(TCPServer):
    headers = {
        'Server': 'CrudeServer',
        'Content-Type': 'text/html',
    }

    status_codes = {
        200: 'OK',
        404: 'Not Found',
        501: 'Not Implemented',
    }

    def handle_request(self, data):

        request = HTTPRequest(data)
        try:
            handler = getattr(self, 'handle_%s' % request.method)
        except AttributeError:
            handler = self.HTTP_501_handler

        response = handler(request)
        return response

    def response_line(self, status_code):

        reason = self.status_codes[status_code]
        line = "HTTP/1.1 %s %s\r\n" % (status_code, reason)
        return line.encode()

    def response_headers(self, extra_headers=None):

        headers_copy = self.headers.copy()

        if extra_headers:
            headers_copy.update(extra_headers)
        headers = ""

        for h in headers_copy:
            headers += "%s: %s\r\n" % (h, headers_copy[h])
        return headers.encode()

    def handle_OPTIONS(self, request):

        response_line = self.response_line(200)

        extra_headers = {'Allow': 'OPTIONS, GET, HEAD, DELETE, POST'}
        response_headers = self.response_headers(extra_headers)

        blank_line = b'\r\n'

        return b''.join([response_line, response_headers, blank_line])

    def handle_GET(self, request):

        path = request.uri.strip('/')

        if not path:
            path = 'index.html'

        if os.path.exists(path) and not os.path.isdir(path):
            response_line = self.response_line(200)

            content_type = mimetypes.guess_type(path)[0] or 'text/html'

            extra_headers = {'Content-Type': content_type}
            response_headers = self.response_headers(extra_headers)

            with open(path, 'rb') as f:
                response_body = f.read()
        else:
            response_line = self.response_line(404)
            response_headers = self.response_headers()
            response_body = b'<h1>404 Not Found</h1>'

        blank_line = b'\r\n'

        response = b''.join([response_line, response_headers, blank_line, response_body])

        return response

    def handle_DELETE(self, request):

        dele = request.uri.strip('/')

        if os.path.exists(dele) and not os.path.isdir(dele):

            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), dele)
            os.remove(path)
            content_type = mimetypes.guess_type(path)[0] or 'text/html'

            extra_headers = {'Content-Type': content_type}
            response_headers = self.response_headers(extra_headers)
            response_line = self.response_line(200)

            response_body = b'<h1>200 File was deleted</h1>'
        elif os.path.isdir(dele):

            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), dele)
            shutil.rmtree(path)

            response_line = self.response_line(200)
            response_headers = self.response_headers()
            response_body = b'<h1>200 Directory was deleted</h1>'
        else:
            response_line = self.response_line(404)
            response_headers = self.response_headers()
            response_body = b'<h1>404 File or directory not found</h1>'

        blank_line = b'\r\n'

        return b''.join([response_line, response_headers, blank_line, response_body])

    def handle_HEAD(self, request):

        path = request.uri.strip('/')

        if not path:
            path = 'index.html'

        if os.path.exists(path) and not os.path.isdir(path):
            response_line = self.response_line(200)

            content_type = mimetypes.guess_type(path)[0] or 'text/html'

            extra_headers = {'Content-Type': content_type}
            response_headers = self.response_headers(extra_headers)

        else:
            response_line = self.response_line(404)
            response_headers = self.response_headers()

        blank_line = b'\r\n'

        response = b''.join([response_line, response_headers, blank_line])

        return response

    def handle_POST(self, request):

        new = request.uri.strip('/')
        content_type = mimetypes.guess_type(new)[0]
        if os.path.exists(new):
            response_line = self.response_line(404)
            response_headers = self.response_headers()
            response_body = b'<h1>404 File or directory already exists</h1>'
        elif not os.path.isdir(new):
            os.mkdir(new)
            response_line = self.response_line(200)
            response_headers = self.response_headers()
            response_body = b'<h1>200 Directory was created</h1>'
        else:
            my_file = open(new, "a+")
            my_file.write("new file")
            my_file.close()
            response_line = self.response_line(200)
            response_headers = self.response_headers()
            response_body = b'<h1>200 Directory was created</h1>'



        blank_line = b'\r\n'

        return b''.join([response_line, response_headers, blank_line, response_body])

    def HTTP_501_handler(self, request):

        response_line = self.response_line(status_code=501)

        response_headers = self.response_headers()

        blank_line = b'\r\n'

        response_body = b'<h1>501 Not Implemented</h1>'

        return b"".join([response_line, response_headers, blank_line, response_body])


class HTTPRequest:

    def __init__(self, data):
        self.method = None
        self.uri = None
        self.http_version = "1.1"
        self.parse(data)

    def parse(self, data):

        lines = data.split(b"\r\n")
        request_line = lines[0]
        words = request_line.split(b" ")

        self.method = words[0].decode()

        if len(words) > 1:
            self.uri = words[1].decode()

        if len(words) > 2:
            self.http_version = words[2]


if __name__ == '__main__':
    server = HTTPServer()
    server.start()
