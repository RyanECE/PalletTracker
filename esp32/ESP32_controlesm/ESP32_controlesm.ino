#include <ESP32Servo.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <WiFiManager.h>  // Vous aurez besoin de la bibliothèque WiFiManager

WiFiUDP udp;
unsigned int localUdpPort = 4210;  // Port sur lequel l'ESP32 écoutera
char incomingPacket[255];

WebServer server(80);
const char* mdnsName = "esp32-device";  // Nom mDNS utilisé pour le programme Python


// Création des objets pour les deux servomoteurs
Servo servoX;
Servo servoY;

// Pins des servomoteurs sur l'ESP32
const int pinServoX = 25; // GPIO 25 pour Servo X
const int pinServoY = 26; // GPIO 26 pour Servo Y

// Dimensions du terrain
float Xmax = 40.0; // Longueur du terrain
float Ymax = 20.0; // Largeur du terrain
float Xcam = Xmax / 2;
float A, B, C;
int X,Y;
// Variables pour les positions actuelles des servos
float currentAngleX = 90; // Position initiale du servo X
float currentAngleY = 90; // Position initiale du servo Y

void setup() {
  // Attacher les servomoteurs aux broches
  servoX.attach(pinServoX, 500, 2400); // Plage PWM pour servos (500-2400 µs)
  servoY.attach(pinServoY, 500, 2400);
  Serial.begin(115200);
  WiFiManager wifiManager;

  // Tente de se connecter au Wi-Fi ou démarre en mode AP si échec
  if (!wifiManager.autoConnect("Wifi Camera")) {
    Serial.println("Failed to connect and hit timeout");
    delay(3000);
    ESP.restart();}
    Serial.println("Connected to WiFi");

  // Initialiser mDNS
  if (!MDNS.begin(mdnsName)) {
    Serial.println("Error setting up mDNS responder!");
    while (1) {
      delay(1000);
    }
  }
  Serial.printf("mDNS responder started: http://%s.local\n", mdnsName);

  udp.begin(localUdpPort);

  // Configurer le serveur web
  server.on("/", handleRoot);
  server.on("/update", handleUpdate);
  server.begin();
  Serial.println("HTTP server started");
  // Routine de mouvement d'initialisation 
  servoX.write(90);
  servoY.write(120);
  delay(1000);
  servoX.write(0);
  servoY.write(120);
  delay(1000);
   servoX.write(180);
  servoY.write(120);
  delay(1000);
  servoX.write(90);
  servoY.write(140);
  Serial.println("Système prêt. Entrez les coordonnées X et Y (format : XxYy).");
}

// Fonction pour déplacer un servomoteur lentement
void moveServoSmooth(Servo &servo, float startAngle, float endAngle, int delayMs) {
  if (startAngle < endAngle) {
    for (float angle = startAngle; angle <= endAngle; angle += 1) {
      servo.write(angle);
      delay(delayMs);
    }
  } else {
    for (float angle = startAngle; angle >= endAngle; angle -= 1) {
      servo.write(angle);
      delay(delayMs);
    }
  }
}

void handleRoot() {
  String html = "<html><body><h1>Configuration WiFi</h1><form action='/update' method='POST'><label for='ssid'>SSID:</label><input type='text' id='ssid' name='ssid'><br><label for='password'>Password:</label><input type='password' id='password' name='password'><br><input type='submit' value='Submit'></form></body></html>";
  server.send(200, "text/html", html);
}

void handleUpdate() {
  String new_ssid = server.arg("ssid");
  String new_password = server.arg("password");

  // Sauvegarder les nouvelles informations de connexion
  WiFi.begin(new_ssid.c_str(), new_password.c_str());

  // Attendre la connexion
  int timeout = 10;  // 10 secondes de délai d'attente
  while (WiFi.status() != WL_CONNECTED && timeout > 0) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
    timeout--;
  }

  if (WiFi.status() == WL_CONNECTED) {
    server.send(200, "text/plain", "Connected to new WiFi. Please restart the ESP.");
  } else {
    server.send(200, "text/plain", "Failed to connect. Please try again.");
  }
}



void loop() {
  server.handleClient();
// Récuperation du packet envoyé par UDP
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = 0;
    }
    Serial.printf("Received packet: %s\n", incomingPacket);
    // Traitez les données ici
  if (strlen(incomingPacket) > 0) {
    // Trouver les positions de 'X' et 'Y' dans le tableau
    char *xPtr = strchr(incomingPacket, 'X');
    char *yPtr = strchr(incomingPacket, 'Y');
   
       if (xPtr != nullptr && yPtr != nullptr) {
      // Extraire les valeurs numériques après 'X' et 'Y'
       X = atoi(xPtr + 1); // Convertir la partie après 'X' en entier
       Y = atoi(yPtr + 1); // Convertir la partie après 'Y' en entier
       }
      float angleX = 0;
      float angleY = 90;

      // Vérifier que les coordonnées sont valides
      // A = Position X du palais par rapport au centre
      // B = Position Y 
      // C = Distance (hypothénuse) entre la camera et le palais
      // Angle x = Angle horizontal de la camera par rapport au palais 
      if (X >= 0 && X <= Xmax && Y >= 0 && Y <= Ymax) {
        if (X < Xcam) {
          A = Xcam - X;
          B = Y;
          C = sqrt((A * A) + (B * B));
          angleX = 180 - (90 - (acos(B / C) * 180 / 3.1415926));
        } else if (X > Xcam) {
          A = X - Xcam;
          B = Y;
          C = sqrt((A * A) + (B * B));
          angleX = (90 - (acos(B / C) * 180 / 3.1415926));
        } else if (X == Xcam) {
          angleX = 90;
        }
        // Gestion de l'angle Y de la camera par seuil 
        if (Y < (Ymax / 4)) {
          angleY = 115;
        } else {
          angleY = 120;
        }

        // Déplacer les servomoteurs avec transition progressive
        moveServoSmooth(servoX, currentAngleX, angleX, 3); // 3 ms de délai entre chaque étape
        moveServoSmooth(servoY, currentAngleY, angleY, 3);

        // Mettre à jour les positions actuelles
        currentAngleX = angleX;
        currentAngleY = angleY;

        // Afficher les résultats
        Serial.println("Commandes exécutées :");
        Serial.print("Servo X (horizontal) -> ");
        Serial.print(angleX);
        Serial.println("°");
        Serial.print("Servo Y (vertical) -> ");
        Serial.print(angleY);
        Serial.println("°");
      } else {
        Serial.println("Erreur : Coordonnées invalides. Assurez-vous que 0 <= X <= Xmax et 0 <= Y <= Ymax.");
      }
    } else {
      Serial.println("Erreur : Format de commande incorrect. Utilisez: XxYy");
    }
  }
}
