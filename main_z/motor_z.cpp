#include "motor_z.h"

volatile long z_ticks = 0;
static long last_z_ticks = 0;
static float z_rpm = 0, z_position_mm = 0;
static unsigned long last_time = 0;

void IRAM_ATTR zEncoderISR() {
  int b = digitalRead(Z_ENC_B);
  z_ticks += (digitalRead(Z_ENC_A) == b) ? 1 : -1;
}

void setupMotorZ() {
  pinMode(Z_PWM, OUTPUT); pinMode(Z_IN1, OUTPUT); pinMode(Z_IN2, OUTPUT);
  pinMode(Z_ENC_A, INPUT_PULLUP); pinMode(Z_ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(Z_ENC_A), zEncoderISR, CHANGE);
  last_time = millis();
}

void stopMotorZ() {
  analogWrite(Z_PWM, 0); digitalWrite(Z_IN1, LOW); digitalWrite(Z_IN2, LOW);
  z_ticks = 0; last_z_ticks = 0; z_rpm = 0; z_position_mm = 0;
}

void setMotorZ_RPM(float rpm) {
  if (fabs(rpm) < 0.01) {
    analogWrite(Z_PWM, 0); digitalWrite(Z_IN1, LOW); digitalWrite(Z_IN2, LOW);
    return;
  }
  int pwm = map(constrain(fabs(rpm), 0, MAX_RPM), 0, MAX_RPM, MIN_PWM, MAX_PWM);
  analogWrite(Z_PWM, pwm);
  if (rpm > 0) { digitalWrite(Z_IN1, HIGH); digitalWrite(Z_IN2, LOW); }
  else         { digitalWrite(Z_IN1, LOW);  digitalWrite(Z_IN2, HIGH); }
}

void getEncoderZ(float* data) {
  unsigned long now = millis();
  float dt = (now - last_time) / 1000.0f;
  if (dt > 0.05) {
    long dz = z_ticks - last_z_ticks;
    z_rpm = ((float)dz / PPR) * (60.0f / dt);
    z_position_mm += dz * PULSE_TO_MM;
    last_z_ticks = z_ticks;
    last_time = now;
  }
  data[0] = z_rpm;
  data[1] = z_position_mm;
}