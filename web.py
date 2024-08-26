import socket
import threading
import os
import json
import datetime

# Загрузка конфигурации
with open('config.json', 'r') as f:
    config = json.load(f)

ALLOWED_EXTENSIONS = ['.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif']


def log_request(client_ip, requested_file, status_code):
    with open('server.log', 'a') as log_file:
        log_file.write(f"{datetime.datetime.now()} - {client_ip} - {requested_file} - {status_code}\n")


def get_content_type(file_path):
    if file_path.endswith(".html"):
        return "text/html"
    elif file_path.endswith(".css"):
        return "text/css"
    elif file_path.endswith(".js"):
        return "application/javascript"
    elif file_path.endswith(".png"):
        return "image/png"
    elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
        return "image/jpeg"
    elif file_path.endswith(".gif"):
        return "image/gif"
    else:
        return "application/octet-stream"


def start_server():
    sock = socket.socket()
    try:
        sock.bind(('', config['port']))
    except OSError as e:
        print(f"Could not bind to port {config['port']}: {e}")
        return

    sock.listen(5)
    server_ip = socket.gethostbyname(socket.gethostname())
    print(f"Server started, listening on port {config['port']}")
    print(f"Open your browser and navigate to:")
    print(f"http://{server_ip}:{config['port']}/1.html")
    print(f"http://{server_ip}:{config['port']}/2.html")

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_request, args=(conn, addr)).start()


def handle_request(conn, addr):
    client_ip = addr[0]
    while True:
        data = conn.recv(config['max_request_size'])
        if not data:
            break
        msg = data.decode()
        print(msg)
        lines = msg.split('\n')
        if len(lines) > 0:
            request_line = lines[0]
            parts = request_line.split(' ')
            if len(parts) >= 2:
                method, path = parts[0], parts[1]
                if method == 'GET':
                    if path == '/':
                        path = '/1.html'
                    file_path = os.path.join(config['working_directory'], path[1:])
                    file_ext = os.path.splitext(file_path)[1]
                    if file_ext not in ALLOWED_EXTENSIONS:
                        send_403(conn)
                        log_request(client_ip, path, 403)
                    else:
                        send_response(conn, file_path, client_ip, path)
                else:
                    send_404(conn)
                    log_request(client_ip, path, 404)
            else:
                send_404(conn)
                log_request(client_ip, path, 404)
        else:
            send_404(conn)
            log_request(client_ip, path, 404)
    conn.close()


def send_response(conn, file_path, client_ip, path):
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
        content_type = get_content_type(file_path)
        response = (
                       f"HTTP/1.1 200 OK\r\n"
                       f"Date: {datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
                       f"Content-Type: {content_type}\r\n"
                       f"Content-Length: {len(content)}\r\n"
                       f"Connection: close\r\n"
                       f"Server: SimplePythonServer\r\n"
                       f"\r\n"
                   ).encode() + content
        conn.send(response)
        log_request(client_ip, path, 200)
    except FileNotFoundError:
        send_404(conn)
        log_request(client_ip, path, 404)


def send_404(conn):
    response = (
        "HTTP/1.1 404 Not Found\r\n"
        "Connection: close\r\n"
        "Server: SimplePythonServer\r\n"
        "\r\n"
        "404 Not Found"
    )
    conn.send(response.encode())


def send_403(conn):
    response = (
        "HTTP/1.1 403 Forbidden\r\n"
        "Connection: close\r\n"
        "Server: SimplePythonServer\r\n"
        "\r\n"
        "403 Forbidden"
    )
    conn.send(response.encode())


if __name__ == '__main__':
    start_server()
