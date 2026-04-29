// main.ino
#include "MotorBridge.h"
#include "WiFiHardware.h"
#include "JOESWiFiSetup.h"
#include <ros.h>
#include <geometry_msgs/Twist.h>
#include <geometry_msgs/Pose2D.h>
#include <std_msgs/Float32MultiArray.h>
#include <std_msgs/String.h>
#include <std_msgs/Int32.h>

// ============================================
// CONFIGURABLE RATES (15 seconds for easy testing)
// ============================================
#define ENCODER_PUBLISH_RATE_MS    15000  // Publish encoder data every 15 seconds
#define DEBUG_PUBLISH_RATE_MS      15000  // Publish debug data every 15 seconds
#define HEARTBEAT_PUBLISH_RATE_MS  15000  // Publish heartbeat every 15 seconds
#define ROS_SPIN_RATE_MS           1000   // Check for incoming messages every 1 second

// ============================================
// ROS Node Handle
// ============================================
ros::NodeHandle_<WiFiHardware> nh;

// ============================================
// PRODUCTION PUBLISHERS (Keep these)
// ============================================
geometry_msgs::Pose2D pose_msg;
ros::Publisher pose_pub("robot_pose", &pose_msg);

std_msgs::Float32MultiArray encoder_msg;
ros::Publisher encoder_pub("motor_encoders", &encoder_msg);

// ============================================
// DEBUG PUBLISHERS (Remove these later)
// ============================================
std_msgs::String debug_msg;
ros::Publisher debug_pub("esp32_debug", &debug_msg);

std_msgs::Int32 heartbeat_msg;
ros::Publisher heartbeat_pub("esp32_heartbeat", &heartbeat_msg);

// ============================================
// PRODUCTION SUBSCRIBERS (Keep these)
// ============================================
float target_left_rpm = 0.0;
float target_right_rpm = 0.0;

void motorCmdCallback(const std_msgs::Float32MultiArray& msg);
ros::Subscriber<std_msgs::Float32MultiArray> motor_sub("motor_commands", &motorCmdCallback);

// ============================================
// DEBUG SUBSCRIBERS (Remove these later)
// ============================================
void debugSubCallback(const std_msgs::String& msg) {
    Serial.println("");
    Serial.println("╔════════════════════════════════════════╗");
    Serial.println("║     📨 MESSAGE RECEIVED FROM ROS      ║");
    Serial.println("╠════════════════════════════════════════╣");
    Serial.printf("║ %-38s ║\n", msg.data);
    Serial.println("╚════════════════════════════════════════╝");
    Serial.println("");
}
ros::Subscriber<std_msgs::String> debug_sub("esp32_command", &debugSubCallback);

// ============================================
// CALLBACK FUNCTIONS
// ============================================
void motorCmdCallback(const std_msgs::Float32MultiArray& msg) {
    if (msg.data_length >= 2) {
        target_left_rpm = msg.data[0];
        target_right_rpm = msg.data[1];
        
        // Direct motor control - no PID on ESP32
        controlMotorsDirect(target_left_rpm, target_right_rpm);
        
        Serial.println("");
        Serial.println("╔════════════════════════════════════════╗");
        Serial.println("║      ⚙️  MOTOR COMMAND RECEIVED       ║");
        Serial.println("╠════════════════════════════════════════╣");
        Serial.printf("║ Left RPM:  %-27.2f ║\n", target_left_rpm);
        Serial.printf("║ Right RPM: %-27.2f ║\n", target_right_rpm);
        Serial.println("╚════════════════════════════════════════╝");
        Serial.println("");
    }
}

void velocityCallback(const geometry_msgs::Twist& msg) {
    Serial.println("[INFO] Received cmd_vel (for reference only)");
}
ros::Subscriber<geometry_msgs::Twist> vel_sub("cmd_vel", &velocityCallback);

// ============================================
// PUBLISH FUNCTIONS
// ============================================
void publishEncoderData() {
    // Publish raw encoder data
    float encoder_data[4];
    getEncoderReadings(encoder_data);
    
    encoder_msg.data = encoder_data;
    encoder_msg.data_length = 4;
    encoder_pub.publish(&encoder_msg);
    
    // Publish pose data
    pose_msg.x = getXPosition();
    pose_msg.y = getYPosition();
    pose_msg.theta = getTheta();
    pose_pub.publish(&pose_msg);
    
    // Fancy debug output to Serial
    Serial.println("");
    Serial.println("╔════════════════════════════════════════╗");
    Serial.println("║       📤 PUBLISHED TO ROS             ║");
    Serial.println("╠════════════════════════════════════════╣");
    Serial.printf("║ Left RPM:   %-25.2f ║\n", encoder_data[0]);
    Serial.printf("║ Right RPM:  %-25.2f ║\n", encoder_data[1]);
    Serial.printf("║ Left Count: %-25.0f ║\n", encoder_data[2]);
    Serial.printf("║ Right Count:%-25.0f ║\n", encoder_data[3]);
    Serial.println("╠════════════════════════════════════════╣");
    Serial.printf("║ Pose X:     %-25.3f ║\n", pose_msg.x);
    Serial.printf("║ Pose Y:     %-25.3f ║\n", pose_msg.y);
    Serial.printf("║ Pose Theta: %-25.2f ║\n", pose_msg.theta * 180/PI);
    Serial.println("╚════════════════════════════════════════╝");
    Serial.println("");
}

// ============================================
// DEBUG FUNCTIONS (Remove these later)
// ============================================
unsigned long last_debug_time = 0;
unsigned long last_heartbeat_time = 0;
int heartbeat_counter = 0;

void publishDebugData() {
    unsigned long current_time = millis();
    
    if (current_time - last_debug_time >= DEBUG_PUBLISH_RATE_MS) {
        char debug_str[100];
        float encoder_data[4];
        getEncoderReadings(encoder_data);
        
        snprintf(debug_str, sizeof(debug_str), 
                "ESP32 Alive! | RPMs: L=%.1f R=%.1f | Pos: (%.2f, %.2f, %.1f°) | Count: %d",
                encoder_data[0], encoder_data[1], 
                getXPosition(), getYPosition(), getTheta() * 180/PI,
                heartbeat_counter);
        
        debug_msg.data = debug_str;
        debug_pub.publish(&debug_msg);
        
        Serial.printf("[DEBUG PUBLISHED] %s\n", debug_str);
        
        last_debug_time = current_time;
    }
}

void publishHeartbeat() {
    unsigned long current_time = millis();
    
    if (current_time - last_heartbeat_time >= HEARTBEAT_PUBLISH_RATE_MS) {
        heartbeat_msg.data = heartbeat_counter;
        heartbeat_pub.publish(&heartbeat_msg);
        
        Serial.printf("[HEARTBEAT #%d] Published to ROS\n", heartbeat_counter);
        
        heartbeat_counter++;
        last_heartbeat_time = current_time;
    }
}

// ============================================
// SETUP
// ============================================
void setup() {
    Serial.begin(115200);
    
    // Initialize hardware
    setupMotorsBridge();
    Serial.println("\n[INFO] Robot HW Setup Complete");
    
    // Setup WiFi and ROS
    Serial.println("[INFO] Setting up Wi-Fi...");
    connectWiFi();
    
    // ============================================
    // ADVERTISE PUBLISHERS
    // ============================================
    nh.advertise(pose_pub);
    nh.advertise(encoder_pub);
    nh.advertise(debug_pub);        // DEBUG
    nh.advertise(heartbeat_pub);    // DEBUG
    
    // ============================================
    // SUBSCRIBE TO TOPICS
    // ============================================
    nh.subscribe(motor_sub);
    nh.subscribe(vel_sub);
    nh.subscribe(debug_sub);        // DEBUG
    
    connectROS();
    
    stopMotorsBridge();
    
    Serial.println("\n");
    Serial.println("╔════════════════════════════════════════╗");
    Serial.println("║   ESP32 COMMUNICATION BRIDGE READY    ║");
    Serial.println("╠════════════════════════════════════════╣");
    Serial.println("║ PUBLISHING (every 15s):               ║");
    Serial.println("║  - /robot_pose (Pose2D)               ║");
    Serial.println("║  - /motor_encoders (Float32MultiArray)║");
    Serial.println("║  - /esp32_debug (String)              ║");
    Serial.println("║  - /esp32_heartbeat (Int32)           ║");
    Serial.println("╠════════════════════════════════════════╣");
    Serial.println("║ SUBSCRIBED:                           ║");
    Serial.println("║  - /motor_commands (Float32MultiArray)║");
    Serial.println("║  - /esp32_command (String)            ║");
    Serial.println("╚════════════════════════════════════════╝");
    Serial.println("");
    Serial.println("📡 Waiting for messages from ROS...");
    Serial.println("📤 Will publish data every 15 seconds");
    Serial.println("");
}

// ============================================
// MAIN LOOP
// ============================================
unsigned long last_encoder_publish = 0;
unsigned long last_ros_spin = 0;

void loop() {
    // Check WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WARNING] Wi-Fi Disconnected. Reconnecting...");
        connectWiFi();
        connectROS();
    }
    
    unsigned long current_time = millis();
    
    // Check for incoming ROS messages every second
    if (current_time - last_ros_spin >= ROS_SPIN_RATE_MS) {
        nh.spinOnce();
        last_ros_spin = current_time;
    }
    
    // Publish encoder data every 15 seconds
    if (current_time - last_encoder_publish >= ENCODER_PUBLISH_RATE_MS) {
        publishEncoderData();
        last_encoder_publish = current_time;
    }
    
    // Publish debug data (DEBUG)
    publishDebugData();
    publishHeartbeat();
    
    delay(10);
}