import tkinter as tk
from tkinter import ttk, messagebox
import paho.mqtt.client as mqtt_client
import json
import threading
import time
from datetime import datetime

class DashboardIoT:
    def __init__(self):
        # Configurações MQTT
        self.broker = 'test.mosquitto.org'
        self.port = 1883
        self.topic_status = "iot/vaga/status"
        self.topic_comando = "iot/vaga/comando"
        self.topic_resposta = "iot/vaga/resposta"
        self.client_id = f"DashboardClient-{int(time.time())}"
        
        # Estado da aplicação
        self.connected = False
        self.last_status = "---"
        self.last_distance = 0
        
        # Configurar interface
        self.setup_ui()
        
        # Configurar MQTT
        self.setup_mqtt()
        
    def setup_ui(self):
        """Configurar interface gráfica"""
        self.app = tk.Tk()
        self.app.title("Dashboard IoT - Sistema de Vaga")
        self.app.geometry("500x600")
        self.app.resizable(False, False)
        
        # Frame principal
        main_frame = ttk.Frame(self.app, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status da conexão
        self.connection_label = ttk.Label(
            main_frame, 
            text="Status MQTT: Desconectado", 
            font=("Arial", 10)
        )
        self.connection_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Status da vaga
        ttk.Label(main_frame, text="Status da Vaga:", font=("Arial", 12, "bold")).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        
        self.status_label = ttk.Label(
            main_frame, 
            text="---", 
            font=("Arial, 16"), 
            foreground="blue"
        )
        self.status_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Distância
        ttk.Label(main_frame, text="Distância:", font=("Arial", 12, "bold")).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        
        self.distance_label = ttk.Label(
            main_frame, 
            text="--- cm", 
            font=("Arial", 14)
        )
        self.distance_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        
        # Seção de comandos
        ttk.Label(main_frame, text="Comandos:", font=("Arial", 12, "bold")).grid(
            row=6, column=0, columnspan=2, sticky=tk.W, pady=(10, 10)
        )
        
        # Botões de comando
        commands_frame = ttk.Frame(main_frame)
        commands_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(
            commands_frame, 
            text="Alerta (LED + Buzzer)", 
            command=lambda: self.enviar_comando("1"),
            width=20
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(
            commands_frame, 
            text="LED Verde", 
            command=lambda: self.enviar_comando("led_verde"),
            width=20
        ).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            commands_frame, 
            text="LED Vermelho", 
            command=lambda: self.enviar_comando("led_vermelho"),
            width=20
        ).grid(row=1, column=0, padx=5, pady=5)
        
        ttk.Button(
            commands_frame, 
            text="Desligar LED", 
            command=lambda: self.enviar_comando("led_off"),
            width=20
        ).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(
            commands_frame, 
            text="Teste Buzzer", 
            command=lambda: self.enviar_comando("teste_buzzer"),
            width=20
        ).grid(row=2, column=0, padx=5, pady=5)
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20
        )
        
        # Log de mensagens
        ttk.Label(main_frame, text="Log de Mensagens:", font=("Arial", 12, "bold")).grid(
            row=9, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        
        # Frame para o log com scrollbar
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, width=50, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Botão para limpar log
        ttk.Button(
            main_frame, 
            text="Limpar Log", 
            command=self.clear_log
        ).grid(row=11, column=0, columnspan=2, pady=10)
        
        # Configurar peso das colunas
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def setup_mqtt(self):
        """Configurar cliente MQTT"""
        try:
            self.client = mqtt_client.Client(client_id=self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # Conectar ao broker
            self.log_message("Tentando conectar ao broker MQTT...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
        except Exception as e:
            self.log_message(f"Erro ao configurar MQTT: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao conectar MQTT: {str(e)}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback de conexão MQTT"""
        if rc == 0:
            self.connected = True
            self.connection_label.config(text="Status MQTT: Conectado", foreground="green")
            self.log_message("Conectado ao broker MQTT!")
            
            # Subscrever aos tópicos
            client.subscribe(self.topic_status)
            client.subscribe(self.topic_resposta)
            self.log_message("Subscrito aos tópicos de status e resposta")
            
        else:
            self.connected = False
            self.connection_label.config(text=f"Status MQTT: Erro ({rc})", foreground="red")
            self.log_message(f"Falha na conexão MQTT: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback de desconexão MQTT"""
        self.connected = False
        self.connection_label.config(text="Status MQTT: Desconectado", foreground="red")
        self.log_message("Desconectado do broker MQTT")
    
    def on_message(self, client, userdata, msg):
        """Callback de mensagem MQTT"""
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            
            self.log_message(f"Recebido [{topic}]: {payload}")
            
            if topic == self.topic_status:
                self.process_status_message(payload)
            elif topic == self.topic_resposta:
                self.log_message(f"Resposta ESP32: {payload}")
                
        except Exception as e:
            self.log_message(f"Erro ao processar mensagem: {str(e)}")
    
    def process_status_message(self, payload):
        """Processar mensagem de status"""
        try:
            # Tentar parsear como JSON
            if payload.startswith('{'):
                data = json.loads(payload)
                status = data.get('status', 'unknown')
                distance = data.get('distancia', 0)
                
                self.last_distance = distance
                self.distance_label.config(text=f"{distance:.1f} cm")
            else:
                # Formato simples (apenas status)
                status = payload.strip()
            
            # Atualizar status
            self.last_status = status
            color = "red" if status == "ocupada" else "green" if status == "disponivel" else "blue"
            self.status_label.config(text=status.upper(), foreground=color)
            
        except json.JSONDecodeError:
            # Se não for JSON, tratar como texto simples
            self.status_label.config(text=payload.upper(), foreground="blue")
    
    def enviar_comando(self, comando):
        """Enviar comando via MQTT"""
        if not self.connected:
            messagebox.showwarning("Aviso", "Não conectado ao broker MQTT!")
            return
        
        try:
            result = self.client.publish(self.topic_comando, comando)
            if result.rc == 0:
                self.log_message(f"Comando enviado: {comando}")
            else:
                self.log_message(f"Erro ao enviar comando: {result.rc}")
                messagebox.showerror("Erro", "Falha ao enviar comando!")
                
        except Exception as e:
            self.log_message(f"Erro ao enviar comando: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao enviar comando: {str(e)}")
    
    def log_message(self, message):
        """Adicionar mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Limpar log de mensagens"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def run(self):
        """Executar aplicação"""
        try:
            self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.app.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
    
    def on_closing(self):
        """Callback ao fechar aplicação"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
        self.app.destroy()

if __name__ == "__main__":
    dashboard = DashboardIoT()
    dashboard.run()