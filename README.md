# Sistema IoT de Monitoramento de Vaga

Sistema completo para monitoramento de vagas de estacionamento usando ESP32, sensor ultrassônico e dashboard Python com comunicação MQTT.

##  Funcionalidades

- **Monitoramento automático** de ocupação de vaga usando sensor ultrassônico
- **LED RGB** para indicação visual do status da vaga
- **Buzzer** para alertas sonoros
- **Dashboard Python** para controle remoto e monitoramento
- **Comunicação MQTT** em tempo real
- **Interface gráfica** intuitiva com log de mensagens

## Componentes

### Hardware (ESP32)
- ESP32
- Sensor ultrassônico HC-SR04
- LED RGB (cátodo comum)
- Buzzer
- Resistores (220Ω para LEDs)

### Software
- Arduino IDE (para ESP32)
- Python 3.x com bibliotecas:
  - `tkinter` (interface gráfica)
  - `paho-mqtt` (comunicação MQTT)

## Como Funciona

### 1. **Detecção Automática**
- O sensor ultrassônico mede a distância a cada 2 segundos
- **Vaga ocupada**: distância < 50cm
- **Vaga disponível**: distância ≥ 50cm
- Status é enviado via MQTT para o dashboard

### 2. **Comunicação MQTT**
- **Broker**: `test.mosquitto.org`
- **Tópicos**:
  - `iot/vaga/status` → Status da vaga (ocupada/disponível)
  - `iot/vaga/comando` → Comandos do dashboard para ESP32
  - `iot/vaga/resposta` → Confirmações do ESP32

### 3. **Comandos Disponíveis**
- `1` → LED amarelo + 3 beeps no buzzer
- `led_verde` → Acende LED verde
- `led_vermelho` → Acende LED vermelho
- `led_off` → Desliga LED
- `teste_buzzer` → Testa buzzer (2 beeps)

##  Configuração

### Dashboard Python
1. Instale as dependências:
```cmd
pip install paho-mqtt
```

2. Execute o dashboard:
```cmd
python dashboard.py
```

##  Como Usar

1. **Inicie o ESP32** no Wokwi
2. **Execute o dashboard** Python
3. **Aguarde a conexão** MQTT (status ficará verde)
4. **Monitore o status** da vaga automaticamente
5. **Use os botões** para enviar comandos remotos
6. **Acompanhe o log** para ver todas as mensagens

## Interface do Dashboard

- **Status da Conexão**: Verde (conectado) / Vermelho (desconectado)
- **Status da Vaga**: 
  - 🔴 OCUPADA (vermelho)
  - 🟢 DISPONÍVEL (verde)
- **Distância**: Valor em centímetros do sensor
- **Botões de Comando**: Controle remoto do LED e buzzer
- **Log de Mensagens**: Histórico em tempo real das comunicações

##  Monitoramento

O sistema monitora automaticamente:
- Distância medida pelo sensor
- Status de ocupação da vaga
- Conexão WiFi do ESP32
- Conexão MQTT do dashboard
- Execução de comandos remotos
