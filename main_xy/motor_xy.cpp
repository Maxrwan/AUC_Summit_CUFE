#include "motor_xy.h"

volatile long x_ticks = 0;
volatile long y_ticks = 0;
static long last_x_ticks = 0;
static long last_y_ticks = 0;
static float x_rpm = 0, y_rpm = 0;
static float x_position_mm = 0, y_position_mm = 0;
static unsigned long last_time = 0;

void IRAM_ATTR xEncoderISR() {
  int b = digitalRead(X_ENC_B);
  x_ticks += (digitalRead(X_ENC_A) == b) ? 1 : -1;
}
void IRAM_ATTR yEncoderISR() {
  int b = digitalRead(Y_ENC_B);
  y_ticks += (digitalRead(Y_ENC_A) == b) ? 1 : -1;
}

void setupMotorsXY() {
  pinMode(X_PWM, OUTPUT); pinMode(X_IN1, OUTPUT); pinMode(X_IN2, OUTPUT);
  pinMode(Y_PWM, OUTPUT); pinMode(Y_IN1, OUTPUT); pinMode(Y_IN2, OUTPUT);
  pinMode(X_ENC_A, INPUT_PULLUP); pinMode(X_ENC_B, INPUT_PULLUP);
  pinMode(Y_ENC_A, INPUT_PULLUP); pinMode(Y_ENC_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(X_ENC_A), xEncoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(Y_ENC_A), yEncoderISR, CHANGE);

  last_time = millis();
  Serial.println("[INFO] XY motors initialized");
}

void stopMotorsXY() {
  analogWrite(X_PWM, 0); digitalWrite(X_IN1, LOW); digitalWrite(X_IN2, LOW);
  analogWrite(Y_PWM, 0); digitalWrite(Y_IN1, LOW); digitalWrite(Y_IN2, LOW);
  x_ticks = y_ticks = 0; last_x_ticks = last_y_ticks = 0;
  x_rpm = y_rpm = 0; x_position_mm = y_position_mm = 0;
}

void setMotorPWM(int pwm_pin, int in1, int in2, float rpm) {
  if (fabs(rpm) < 0.01) {
    analogWrite(pwm_pin, 0);
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
    return;
  }
  int pwm = map(constrain(fabs(rpm), 0, MAX_RPM), 0, MAX_RPM, MIN_PWM, MAX_PWM);
  pwm = constrain(pwm, MIN_PWM, MAX_PWM);
  analogWrite(pwm_pin, pwm);
  if (rpm > 0) {
    digitalWrite(in1, HIGH); digitalWrite(in2, LOW);
  } else {
    digitalWrite(in1, LOW); digitalWrite(in2, HIGH);
  }
}

void setMotorX_RPM(float rpm) { setMotorPWM(X_PWM, X_IN1, X_IN2, rpm); }
void setMotorY_RPM(float rpm) { setMotorPWM(Y_PWM, Y_IN1, Y_IN2, rpm); }

void getEncoderXY(float* data) {
  unsigned long now = millis();
  float dt = (now - last_time) / 1000.0f;
  if (dt > 0.05) {   // update every 50ms
    long dx = x_ticks - last_x_ticks;
    long dy = y_ticks - last_y_ticks;
    x_rpm = ((float)dx / PPR) * (60.0f / dt);
    y_rpm = ((float)dy / PPR) * (60.0f / dt);
    x_position_mm += dx * PULSE_TO_MM;
    y_position_mm += dy * PULSE_TO_MM;
    last_x_ticks = x_ticks;
    last_y_ticks = y_ticks;
    last_time = now;
  }
  data[0] = x_rpm;
  data[1] = y_rpm;
  data[2] = x_position_mm;
  data[3] = y_position_mm;
}