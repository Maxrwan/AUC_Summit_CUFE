#ifndef MOTOR_Z_H
#define MOTOR_Z_H
#include <Arduino.h>

#define Z_PWM  23
#define Z_IN1  22
#define Z_IN2  21
#define Z_ENC_A 13
#define Z_ENC_B 14

#define PPR 2002.7
#define PULSE_TO_MM 0.09725807386
#define MAX_PWM 220
#define MIN_PWM 80
#define MAX_RPM 200.0f

void setupMotorZ();
void stopMotorZ();
void setMotorZ_RPM(float rpm);
void getEncoderZ(float* data);  // data[2] = {z_rpm, z_position_mm}
#endif