#include <WiFi.h>
#include <PubSubClient.h>

// Credenciais WiFi
const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* mqtt_server = "test.mosquitto.org";

WiFiClient espClient;
PubSubClient client(espClient);

// Pinos
const int rgbLedPinR = 16;
const int rgbLedPinG = 17;
const int rgbLedPinB = 18;
const int trig_pin = 5;
const int echo_pin = 19;
const int buzzer = 21;

// Configurações PWM
const int freq = 5000;      // Frequência PWM
const int resolution = 8;   // Resolução de 8 bits (0-255)

// Variáveis do sensor
long duration;
float distance_cm;
unsigned long lastMeasurement = 0;
const unsigned long measurementInterval = 2000; // 2 segundos

void setup() {
  Serial.begin(115200);
  
  // Configurar pinos
  pinMode(trig_pin, OUTPUT);
  pinMode(echo_pin, INPUT);
  pinMode(buzzer, OUTPUT);
  
  // Configurar PWM para LEDs RGB (versão nova da API)
  ledcAttach(rgbLedPinR, freq, resolution);
  ledcAttach(rgbLedPinG, freq, resolution);
  ledcAttach(rgbLedPinB, freq, resolution);
  
  // Inicializar LED apagado
  set_color(0, 0, 0);
  
  // Conectar WiFi e MQTT
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  
  Serial.println("ESP32 inicializado com sucesso!");
}

void loop() {
  // Manter conexão MQTT
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Medir distância a cada intervalo definido
  unsigned long currentTime = millis();
  if (currentTime - lastMeasurement >= measurementInterval) {
    get_distance();
    lastMeasurement = currentTime;
  }
  
  delay(100); // Pequeno delay para não sobrecarregar o loop
}

void setup_wifi() {
  delay(10);
  Serial.print("Conectando ao WiFi");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Conectando ao MQTT...");
    
    // Criar ID único para o cliente
    String client_id = "ESP32Client-" + String(WiFi.macAddress());
    
    if (client.connect(client_id.c_str())) {
      Serial.println(" conectado!");
      
      // Subscrever ao tópico de comandos
      if (client.subscribe("iot/vaga/comando")) {
        Serial.println("Subscrito ao tópico de comandos");
      }
      
      // Publicar status de conexão
      client.publish("iot/vaga/status", "ESP32 conectado");
      
    } else {
      Serial.print(" falha, rc=");
      Serial.print(client.state());
      Serial.println(" tentando novamente em 5 segundos");
      delay(5000);
    }
  }
}

void get_distance() {
  // Enviar pulso ultrassônico
  digitalWrite(trig_pin, LOW);
  delayMicroseconds(2);
  digitalWrite(trig_pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_pin, LOW);
  
  // Medir duração do eco
  duration = pulseIn(echo_pin, HIGH, 30000); // Timeout de 30ms
  
  if (duration > 0) {
    distance_cm = duration * 0.034 / 2;
    
    // Determinar status da vaga
    String status = (distance_cm < 50) ? "ocupada" : "disponivel";
    
    Serial.printf("Distância: %.1f cm - Vaga: %s\n", distance_cm, status.c_str());
    
    // Publicar status via MQTT
    String payload = "{\"status\":\"" + status + "\",\"distancia\":" + String(distance_cm) + "}";
    client.publish("iot/vaga/status", payload.c_str());
    
  } else {
    Serial.println("Erro na leitura do sensor ultrassônico");
  }
}

void set_color(int vermelho, int verde, int azul) {
  // Para LED RGB cátodo comum, inverter valores
  vermelho = 255 - vermelho;
  verde = 255 - verde;
  azul = 255 - azul;
  
  // Aplicar PWM diretamente aos pinos (nova API)
  ledcWrite(rgbLedPinR, vermelho);
  ledcWrite(rgbLedPinG, verde);
  ledcWrite(rgbLedPinB, azul);
  
  Serial.printf("LED RGB: R=%d, G=%d, B=%d\n", vermelho, verde, azul);
}

void buzzer_beep(int frequency, int duration_ms, int repetitions) {
  for (int i = 0; i < repetitions; i++) {
    // Gerar tom no buzzer (nova API)
    ledcAttach(buzzer, frequency, 8);
    ledcWrite(buzzer, 128); // 50% duty cycle
    
    delay(duration_ms);
    
    // Parar som
    ledcWrite(buzzer, 0);
    
    if (i < repetitions - 1) {
      delay(200); // Pausa entre beeps
    }
  }
  
  // Desanexar buzzer do PWM
  ledcDetach(buzzer);
}

void callback(char* topic, byte* payload, unsigned int length) {
  // Converter payload para string
  String comando = "";
  for (unsigned int i = 0; i < length; i++) {
    comando += (char)payload[i];
  }
  
  Serial.println("Tópico: " + String(topic));
  Serial.println("Comando recebido: " + comando);
  
  // Processar comandos
  if (comando == "1") {
    Serial.println("Executando comando 1: LED amarelo + buzzer");
    
    // Acender LED amarelo
    set_color(255, 255, 0);
    
    // Tocar buzzer 3 vezes
    buzzer_beep(800, 500, 3);
    
    // Apagar LED
    set_color(0, 0, 0);
    
    // Confirmar execução
    client.publish("iot/vaga/resposta", "Comando 1 executado");
    
  } else if (comando == "led_verde") {
    set_color(0, 255, 0);
    client.publish("iot/vaga/resposta", "LED verde acionado");
    
  } else if (comando == "led_vermelho") {
    set_color(255, 0, 0);
    client.publish("iot/vaga/resposta", "LED vermelho acionado");
    
  } else if (comando == "led_off") {
    set_color(0, 0, 0);
    client.publish("iot/vaga/resposta", "LED desligado");
    
  } else if (comando == "teste_buzzer") {
    buzzer_beep(1000, 200, 2);
    client.publish("iot/vaga/resposta", "Teste buzzer executado");
    
  } else {
    Serial.println("Comando não reconhecido: " + comando);
    client.publish("iot/vaga/resposta", "Comando não reconhecido");
  }
}