#include <SPI.h>
#include "DW1000Ranging.h"
#include "DW1000.h"
#include <WiFi.h>
#include <WiFiUdp.h>
#include <PubSubClient.h>
#include <WiFiManager.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <EEPROM.h>

#define EEPROM_SIZE 512

// Anchor configuration
uint16_t anchors[] = {
  0x84,  // Anchor 1
  0x85,  // Anchor 2
  0x86   // Anchor 3
};

char* anchor_addresses[] = {
  "84:00:5B:D5:A9:9A:E2:9C",
  "85:00:5B:D5:A9:9A:E2:9C",
  "86:00:5B:D5:A9:9A:E2:9C"
};

// SPI and DW1000 configuration
#define SPI_SCK 18
#define SPI_MISO 19
#define SPI_MOSI 23
#define DW_CS 4

const uint8_t PIN_RST = 27;
const uint8_t PIN_IRQ = 34;
const uint8_t PIN_SS = 4;

// Network configuration
const int udp_local_port = 12345;    // Local UDP port
const char* mqtt_topic = "pallet/rollerhockey"; // MQTT topic
const int mqtt_port = 1883;          // MQTT port
bool ready_to_send_mqtt = false;     // Indicates if ESP is ready to send MQTT
bool mqtt_sending_active = false;    // Indicates if MQTT sending is active

// Client instances
WiFiClient espClient;
PubSubClient client(espClient);  // MQTT client
WiFiManager wifiManager;         // WiFiManager for easy WiFi connection
WiFiUDP udp;                     // UDP client for local communication
WebServer server(80);            // Web server to handle configuration

// Global variables
float lastDistances[3] = { 0.0, 0.0, 0.0 }; // Last measured distances
unsigned long lastUpdate = 0;  // Last MQTT update time
char buffer[100];              // Buffer for MQTT messages
IPAddress mqtt_server_ip;      // MQTT server IP address
char udp_buffer[255];          // UDP message buffer

// Function to connect to WiFi via WiFiManager
void setup_wifi() {
  if (!wifiManager.autoConnect("protoPalet")) {
    Serial.println("Connection failed - restarting");
    delay(3000);
    ESP.restart();
  }

  Serial.println("Connected to WiFi");
  Serial.print("📡 IP: ");
  Serial.println(WiFi.localIP());
}

// Function to connect ESP to MQTT
bool connect_mqtt() {
  if (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    if (client.connect("palet")) {
      Serial.println("Connected to Mosquitto!");
      return true;
    } else {
      Serial.println("MQTT connection failed");
      return false;
    }
  }
  return true;
}

void setup() {
  Serial.begin(115200);  // Initialize serial communication
  delay(1000);

  // WiFi configuration
  setup_wifi();

  // UDP initialization
  udp.begin(udp_local_port);
  Serial.print("📡 UDP ready on port: ");
  Serial.println(udp_local_port);

  // SPI initialization
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);

  // DW1000 initialization
  DW1000Ranging.initCommunication(PIN_RST, PIN_SS, PIN_IRQ);
  DW1000Ranging.attachNewRange(newRange);  // Attach callback for new range measurements
  DW1000Ranging.attachNewDevice(newDevice);  // Attach callback for new devices
  DW1000Ranging.attachInactiveDevice(inactiveDevice);  // Attach callback for inactive devices

  // DW1000 devices initialization
  DW1000Device devices[3];
  for (int i = 0; i < 3; i++) {
    devices[i].setAddress(anchor_addresses[i]);  // Set anchor addresses
    DW1000Ranging.addNetworkDevices(&devices[i]); // Add each anchor to the network
  }

  // Start in "Tag" mode with the first anchor
  DW1000Ranging.startAsTag(anchor_addresses[0], DW1000.MODE_LONGDATA_RANGE_LOWPOWER, false);
}

// Callback function for when a new device is added
void newDevice(DW1000Device* device) {
  Serial.print("Device added: ");
  Serial.println(device->getShortAddress(), HEX);
}

// Callback function for when a device becomes inactive
void inactiveDevice(DW1000Device* device) {
  Serial.print("Device inactive: ");
  Serial.println(device->getShortAddress(), HEX);
}

// Function to send data via MQTT
void sendMQTTUpdate() {
  if (!client.connected() || !mqtt_sending_active) return;

  static unsigned long lastPrint = 0;
  static int messageCount = 0;
  messageCount++;

  // Display statistics every second
  if (millis() - lastPrint >= 1000) {
    Serial.printf("Messages sent per second: %d\n", messageCount);
    messageCount = 0;
    lastPrint = millis();
  }

  // Message format: "84:1.86;85:1.59;86:1.33"
  snprintf(buffer, sizeof(buffer), "%02X:%.2f;%02X:%.2f;%02X:%.2f",
           anchors[0], lastDistances[0],
           anchors[1], lastDistances[1],
           anchors[2], lastDistances[2]);

  client.publish(mqtt_topic, buffer);  // Send data via MQTT
  Serial.println(buffer);  // Display the sent message
}

// Function to handle UDP discovery
void handleUDPDiscovery() {
  if (!ready_to_send_mqtt) {
    Serial.println("📤 Sending UDP request to get IP...");
    udp.beginPacket("255.255.255.255", udp_local_port);
    udp.print("REQUEST_IP");
    udp.endPacket();

    delay(1000);
    int packet_size = udp.parsePacket();

    if (packet_size) {
      udp.read(udp_buffer, 255);
      udp_buffer[packet_size] = 0;
      String received = String(udp_buffer);

      if (received != "deconnect") {
        if (mqtt_server_ip.fromString(received)) {
          Serial.printf("MQTT IP configured: %s\n", received.c_str());
          client.setServer(mqtt_server_ip, mqtt_port);  // Set MQTT server IP address
          ready_to_send_mqtt = true;  // Prepare to send MQTT data
          Serial.println("Waiting for start signal...");
        }
      }
    }
  }
}

// Function to handle UDP control signals (start, stop, etc.)
void handleUDPControl() {
  int packet_size = udp.parsePacket();
  if (packet_size) {
    char control_buffer[10];
    udp.read(control_buffer, packet_size);
    control_buffer[packet_size] = 0;
    String signal = String(control_buffer);

    if (signal == "deconnect") {
      Serial.println("Disconnect signal received");
      if (client.connected()) {
        client.disconnect();  // Disconnect from MQTT
      }
      ready_to_send_mqtt = false;
      mqtt_sending_active = false;
    } else if (signal == "start") {
      Serial.println("✅ Start signal received");
      mqtt_sending_active = true;  // Activate MQTT data sending
    } else if (signal == "stop") {
      Serial.println("Stop signal received");
      mqtt_sending_active = false;  // Deactivate MQTT data sending
    }
  }
}

// Function called when a new range measurement is received
void newRange() {
  DW1000Device* device = DW1000Ranging.getDistantDevice();
  if (!device) return;

  float range = device->getRange();
  if (range < 0) return;   // Ignore negative measurements
  if (range > 50) return;  // Ignore excessively large measurements

  // Identify which anchor sent the measurement
  uint16_t address = device->getShortAddress();
  for (int i = 0; i < 3; i++) {
    if (anchors[i] == address) {
      lastDistances[i] = range;  // Store the range for the corresponding anchor
      break;
    }
  }

  // Send an MQTT update every 100ms
  unsigned long now = mill
