#ifndef MOTOR_XY_H
#define MOTOR_XY_H

#include <Arduino.h>

// ---------- Motor X ----------
#define X_PWM  4
#define X_IN1  16
#define X_IN2  17
#define X_ENC_A 26
#define X_ENC_B 27

// ---------- Motor Y ----------
#define Y_PWM  5
#define Y_IN1  18
#define Y_IN2  19
#define Y_ENC_A 13
#define Y_ENC_B 14

// Mechanism constants
#define PPR 2002.7
#define PULSE_TO_MM 0.09725807386
#define MAX_PWM 220
#define MIN_PWM 80
#define MAX_RPM 200.0f   // adjust as needed
#define PI 3.14159265

void setupMotorsXY();
void stopMotorsXY();
void setMotorX_RPM(float rpm);
void setMotorY_RPM(float rpm);
void getEncoderXY(float* data);  // data[4] = {x_rpm, y_rpm, x_position_mm, y_position_mm}

#endif