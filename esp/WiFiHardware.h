#ifndef WIFI_HARDWARE_H
#define WIFI_HARDWARE_H

#include <WiFi.h>
#include <Arduino.h>

class WiFiHardware {
public:
    WiFiHardware() {}

    void init() {
        client.connect(server, port);
    }

    void setConnection(IPAddress &server, int port) {
        this->server = server;
        this->port = port;
    }

    int read() {
        if (client.connected()) {
            return client.read();
        }

        // Attempt to reconnect if not connected
        client.connect(server, port);
        return -1;
    }

    void write(uint8_t* data, int length) {
        for (int i = 0; i < length; i++) {
            client.write(data[i]);
        }
    }

    unsigned long time() {
        return millis();
    }

protected:
    WiFiClient client;       // WiFi client object (not a pointer)
    IPAddress server;        // Server IP address
    uint16_t port;           // Server port
};

#endif