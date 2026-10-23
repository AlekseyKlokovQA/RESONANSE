import os
import sys
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

MAX_CONCURRENT_USERS = 5
active_connections_lock = threading.Lock()
current_active_users = 0

class LimitedRangeRequestHandler(SimpleHTTPRequestHandler):
    def handle_one_request(self):
        global current_active_users
        with active_connections_lock:
            if current_active_users >= MAX_CONCURRENT_USERS:
                # Reject 6th concurrent user with HTTP 503
                self.send_response(503, "Service Unavailable (Max 5 Users Limit)")
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Retry-After', '5')
                self.end_headers()
                
                limit_html_path = os.path.join(os.path.dirname(__file__), 'temp_server', 'limit_exceeded.html')
                if not os.path.exists(limit_html_path):
                    limit_html_path = os.path.join(os.path.dirname(__file__), 'limit_exceeded.html')

                if os.path.exists(limit_html_path):
                    with open(limit_html_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.wfile.write(b"<h1>503 Server Busy</h1><p>Maximum 5 concurrent testing users limit reached. Please wait.</p>")
                return

            current_active_users += 1

        try:
            super().handle_one_request()
        finally:
            with active_connections_lock:
                current_active_users = max(0, current_active_users - 1)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            parts = [p for p in self.path.split('/') if p]
            if not parts or parts[-1] == '':
                for index in "index.html", "index.htm":
                    index_path = os.path.join(path, index)
                    if os.path.exists(index_path):
                        path = index_path
                        break

        if not os.path.isfile(path):
            return super().send_head()

        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        size = fs.st_size

        # Handle Range header (for audio .mp3 scrubbing)
        range_header = self.headers.get('Range')
        if range_header and range_header.startswith('bytes='):
            try:
                ranges = range_header[6:].split('-')
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else size - 1
                if start >= size:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    f.close()
                    return None
                end = min(end, size - 1)
                length = end - start + 1

                self.send_response(206, "Partial Content")
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                f.seek(start)
                return f
            except Exception:
                pass

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return f

def run():
    # Guarantee working directory is the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    server_address = ('0.0.0.0', port)
    
    # Threading server to handle simultaneous users cleanly
    from socketserver import ThreadingMixIn
    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    try:
        httpd = ThreadedHTTPServer(server_address, LimitedRangeRequestHandler)
    except Exception as e:
        print(f"\n[ОШИБКА]: Не удалось запустить сервер на порту {port}: {e}")
        print(f"Возможно, порт {port} уже занят другой программой.")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

    print(f"===========================================================", flush=True)
    print(f" ВРЕМЕННЫЙ ТЕСТОВЫЙ СЕРВЕР «РЕЗОНАНС» УСПЕШНО ЗАПУЩЕН", flush=True)
    print(f"===========================================================", flush=True)
    print(f" 1. Главная страница:     http://localhost:{port}", flush=True)
    print(f" 2. Личный кабинет:       http://localhost:{port}/profile.html", flush=True)
    print(f" 3. Локальный IP:         http://127.0.0.1:{port}", flush=True)
    print(f"-----------------------------------------------------------", flush=True)
    print(f" ОГРАНИЧЕНИЕ: СТРОГО ДО {MAX_CONCURRENT_USERS} ОДНОВРЕМЕННЫХ ПОЛЬЗОВАТЕЛЕЙ", flush=True)
    print(f" Чтобы остановить сервер: нажмите Ctrl + C в терминале", flush=True)
    print(f"===========================================================", flush=True)
    print(f"Открытие браузера...", flush=True)

    def open_browser():
        import time
        time.sleep(0.8)
        try:
            webbrowser.open(f'http://localhost:{port}')
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер тестирования остановлен без остатка процессов.", flush=True)

if __name__ == '__main__':
    run()
