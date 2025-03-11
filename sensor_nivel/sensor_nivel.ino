#include <Arduino.h>
#include <stdio.h>
#include <SoftwareSerial.h>
#include <EBYTE.h>
#include <hcsr04.h>

/*
    LoRa           Arduino
    Vcc ----------> 3.3V
    Gnd ----+-----> Gnd
            ↑
            2kΩ    !! IMPORTANT to prevent the module from burning out !!
            ↑
    Rx  ----+-1kΩ-> Tx(Arduino)
    Tx  ----------> Rx(Arduino)
    AUX ----------> any digital pin
    M1  ----------> any digital pin
    MO  ----------> any digital pin
*/
#define PIN_LORA_AUX 12
#define PIN_LORA_TX 11
#define PIN_LORA_RX 10
#define PIN_LORA_M1 9
#define PIN_LORA_M0 8

#define PIN_ARDUINO_RX PIN_LORA_TX/* Arduino RX, connect to LoRa TX */
#define PIN_ARDUINO_TX PIN_LORA_RX/* Arduino TX, connect to LoRa RX */

SoftwareSerial ESerial(PIN_ARDUINO_RX, PIN_ARDUINO_TX); // create serial port
EBYTE Transceiver(&ESerial, PIN_LORA_M0, PIN_LORA_M1, PIN_LORA_AUX); // create the transceiver object


/*
    HC-SR04     Arduino
    Vcc ----------> 5V
    Gnd ----------> Gnd
*/
#define PIN_TRIG 4
#define PIN_ECHO 3

//             trigger, echo,    min, max 
HCSR04 hcsr04(PIN_TRIG, PIN_ECHO, -1, -1);

#define BUF_SIZE 1024
int lastDistance = -1;
char txt[BUF_SIZE];

void setup() {
    Serial.begin(9600); // Arduino

    ESerial.begin(9600); // LoRa

    Serial.println("Starting...");

    Transceiver.init(); // set the pinMode

    Transceiver.PrintParameters(); // print parameters
}

void loop() {
    int currentDistance = (int) round(hcsr04.distanceInMillimeters() / 10); // cm

    if (currentDistance != lastDistance) {
        lastDistance = currentDistance;
        snprintf(txt, BUF_SIZE, "{distance:%d}\n", currentDistance);

        Serial.print("Sending: ");
        Serial.println(txt);

        // Allow transmissions and sends a preamble to waken receiver (in MODE_POWERDOWN)
        Transceiver.SetMode(MODE_WAKEUP);
        Transceiver.SendStruct(&txt, strlen(txt));
    }
    // Power saving mode. Can't transmit but can receive if transmitter is in wake up mode
    Transceiver.SetMode(MODE_POWERDOWN);
    delay(10000); // ms → 10s
}
