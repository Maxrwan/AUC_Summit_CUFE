// MotorBridge.cpp
#include "MotorBridge.h"
#include <math.h>

// Encoder State
volatile long right_encoder_ticks = 0;
volatile long left_encoder_ticks = 0;
volatile long last_right_ticks = 0;
volatile long last_left_ticks = 0;

// Motor State
float left_rpm = 0.0;
float right_rpm = 0.0;

// Pose State
float x_position = 0.0;
float y_position = 0.0;
float theta_encoder = 0.0;

// Timing
unsigned long last_encoder_time = 0;

// Interrupt Service Routines
void IRAM_ATTR rightEncoderISR() {
    int direction = digitalRead(RIGHT_ENCODER_DIRECTION);
    right_encoder_ticks += (direction ? -1 : 1);
}

void IRAM_ATTR leftEncoderISR() {
    int direction = digitalRead(LEFT_ENCODER_DIRECTION);
    left_encoder_ticks += (direction ? 1 : -1);
}

void setupMotorsBridge() {
    // Motor pins
    pinMode(ENA, OUTPUT);
    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
    pinMode(ENB, OUTPUT);
    pinMode(IN3, OUTPUT);
    pinMode(IN4, OUTPUT);
    
    // Encoder pins
    pinMode(RIGHT_ENCODER_INTERRUPT, INPUT_PULLUP);
    pinMode(RIGHT_ENCODER_DIRECTION, INPUT_PULLUP);
    pinMode(LEFT_ENCODER_INTERRUPT, INPUT_PULLUP);
    pinMode(LEFT_ENCODER_DIRECTION, INPUT_PULLUP);
    
    // Attach interrupts
    attachInterrupt(digitalPinToInterrupt(RIGHT_ENCODER_INTERRUPT), rightEncoderISR, RISING);
    attachInterrupt(digitalPinToInterrupt(LEFT_ENCODER_INTERRUPT), leftEncoderISR, RISING);
    
    // Initialize timing
    last_encoder_time = millis();
    
    // Reset state
    x_position = 0;
    y_position = 0;
    theta_encoder = 0;
    
    Serial.println("[INFO] Motor Bridge Initialized");
}

void stopMotorsBridge() {
    analogWrite(ENA, 0);
    analogWrite(ENB, 0);
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    
    // Reset encoder counts
    right_encoder_ticks = 0;
    left_encoder_ticks = 0;
    last_right_ticks = 0;
    last_left_ticks = 0;
    
    // Reset pose
    x_position = 0;
    y_position = 0;
    theta_encoder = 0;
    
    left_rpm = 0;
    right_rpm = 0;
    
    Serial.println("[INFO] Motors Stopped and State Reset");
}

void controlMotorsDirect(float left_target_rpm, float right_target_rpm) {
    // Convert RPM to PWM (simple linear mapping)
    int pwm_right = 0;
    int pwm_left = 0;
    
    if (fabs(right_target_rpm) > 0) {
        pwm_right = map(constrain(fabs(right_target_rpm), 0, 100), 0, 100, 40, 255);
    }
    
    if (fabs(left_target_rpm) > 0) {
        pwm_left = map(constrain(fabs(left_target_rpm), 0, 100), 0, 100, 40, 255);
    }
    
    // Right motor
    analogWrite(ENA, pwm_right);
    if (right_target_rpm > 0) {
        digitalWrite(IN1, HIGH);
        digitalWrite(IN2, LOW);
    } else if (right_target_rpm < 0) {
        digitalWrite(IN1, LOW);
        digitalWrite(IN2, HIGH);
    } else {
        digitalWrite(IN1, LOW);
        digitalWrite(IN2, LOW);
    }
    
    // Left motor
    analogWrite(ENB, pwm_left);
    if (left_target_rpm > 0) {
        digitalWrite(IN3, HIGH);
        digitalWrite(IN4, LOW);
    } else if (left_target_rpm < 0) {
        digitalWrite(IN3, LOW);
        digitalWrite(IN4, HIGH);
    } else {
        digitalWrite(IN3, LOW);
        digitalWrite(IN4, LOW);
    }
}

void getEncoderReadings(float* data) {
    // Calculate RPMs
    unsigned long current_time = millis();
    float delta_time = (current_time - last_encoder_time) / 1000.0; // seconds
    
    if (delta_time > 0.05) { // Update every 50ms
        long delta_right = right_encoder_ticks - last_right_ticks;
        long delta_left = left_encoder_ticks - last_left_ticks;
        
        right_rpm = ((float)delta_right / PPR) * (60.0 / delta_time);
        left_rpm = ((float)delta_left / PPR) * (60.0 / delta_time);
        
        last_right_ticks = right_encoder_ticks;
        last_left_ticks = left_encoder_ticks;
        last_encoder_time = current_time;
        
        // Update pose
        updatePoseBridge();
    }
    
    // Return data array
    data[0] = left_rpm;
    data[1] = right_rpm;
    data[2] = (float)left_encoder_ticks;
    data[3] = (float)right_encoder_ticks;
}

void updatePoseBridge() {
    static unsigned long last_pose_time = 0;
    unsigned long current_time = millis();
    float delta_time = (current_time - last_pose_time) / 1000.0;
    last_pose_time = current_time;
    
    if (delta_time > 0) {
        // Calculate distances moved
        float left_distance = (left_encoder_ticks * (2 * PI * WHEEL_RADIUS) / PPR);
        float right_distance = (right_encoder_ticks * (2 * PI * WHEEL_RADIUS) / PPR);
        
        float distance = (right_distance + left_distance) / 2.0;
        float delta_theta = (right_distance - left_distance) / WHEEL_DISTANCE;
        
        theta_encoder += delta_theta;
        
        // Update position
        x_position += distance * cos(theta_encoder);
        y_position += distance * sin(theta_encoder);
    }
}

float getXPosition() {
    return x_position;
}

float getYPosition() {
    return y_position;
}

float getTheta() {
    return theta_encoder;
}