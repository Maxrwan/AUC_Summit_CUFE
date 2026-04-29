// MotorBridge.h
#ifndef MOTOR_BRIDGE_H
#define MOTOR_BRIDGE_H

#include <Arduino.h>

// Pin Definitions
#define ENA 4   // Right motor PWM
#define IN1 16  // Right motor direction 1
#define IN2 17  // Right motor direction 2
#define ENB 5   // Left motor PWM
#define IN3 18  // Left motor direction 1
#define IN4 19  // Left motor direction 2

// Encoder pins
#define RIGHT_ENCODER_INTERRUPT 26
#define RIGHT_ENCODER_DIRECTION 27
#define LEFT_ENCODER_INTERRUPT 32
#define LEFT_ENCODER_DIRECTION 33

// Constants for encoder calculations
#define WHEEL_RADIUS 0.034   // meters
#define WHEEL_DISTANCE 0.18  // meters
#define PPR 517              // Pulses Per Revolution
#define GEAR_RATIO 47.0      // Gear ratio
#define PI 3.14159

// Function Declarations
void setupMotorsBridge();
void stopMotorsBridge();
void controlMotorsDirect(float left_rpm, float right_rpm);
void getEncoderReadings(
    float* data);  // data[4] = {left_rpm, right_rpm, left_count, right_count}
void updatePoseBridge();
float getXPosition();
float getYPosition();
float getTheta();

#endif