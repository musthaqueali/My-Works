import http.server
import socketserver
import os
import sys
import webbrowser
import threading
import time
import shutil

class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Handler with byte range support for smooth PDF streaming."""
    
    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def copyfile(self, source, outputfile):
        try:
            shutil.copyfileobj(source, outputfile)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def send_head(self):
        """Common code for GET and HEAD commands with Range support."""
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            parts = sys.version_info
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return super().send_head()
        
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            size = fs.st_size
            
            # Check for Range header
            range_header = self.headers.get('Range')
            if range_header and range_header.startswith('bytes='):
                ranges = range_header[6:].split('-')
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else size - 1
                if start >= size or end >= size or start > end:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    f.close()
                    return None
                
                self.send_response(206)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()
                
                f.seek(start)
                return RangeFileWrapper(f, end - start + 1)
            
            self.send_response(200)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(size))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except Exception:
            f.close()
            raise

class RangeFileWrapper:
    def __init__(self, f, length):
        self.f = f
        self.remaining = length

    def read(self, size=-1):
        if self.remaining <= 0:
            return b""
        if size < 0 or size > self.remaining:
            size = self.remaining
        data = self.f.read(size)
        self.remaining -= len(data)
        return data

    def close(self):
        self.f.close()

def start_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = 8000
    for p in range(8000, 8030):
        try:
            httpd = socketserver.TCPServer(("", p), RangeRequestHandler)
            port = p
            break
        except OSError:
            continue

    url = f"http://localhost:{port}/index.html"
    print("=" * 65)
    print("  THE 100 DAYS OF MACHINE LEARNING DISPATCH")
    print("  Broadsheet & Parchment Study Portal")
    print("=" * 65)
    print(f"\n  Serving from: {os.getcwd()}")
    print(f"  URL: {url}\n")
    print("  [✓] Streaming Range Requests Enabled")
    print("  [✓] Direct Continuous Scrolling Ready")
    print("  [✓] Instant 0.0s Topic Navigation Active\n")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 65 + "\n")

    def open_browser():
        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dispatch server...")
        httpd.shutdown()

if __name__ == "__main__":
    start_server()
