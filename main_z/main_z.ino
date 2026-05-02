// main_z.ino
#include "motor_z.h"              // setupMotorZ(), setMotorZ_RPM(), getEncoderZ()
#include "WiFiHardware.h"

// ----- IP for this ESP ---------------------------------
#include "JOESWiFiSetup.h"

// ----- Required by JOESWiFiSetup.h ----------------------
ros::NodeHandle_<WiFiHardware> nh;
void dummyVelCB(const geometry_msgs::Twist& msg) { /* unused */ }
ros::Subscriber<geometry_msgs::Twist> vel_sub("cmd_vel", &dummyVelCB);
geometry_msgs::Pose2D pose_msg;
ros::Publisher pose_pub("robot_pose", &pose_msg);

// ============================================================
// RATES
// ============================================================
#define ENCODER_PUBLISH_RATE_MS    50
#define DEBUG_PUBLISH_RATE_MS      5000
#define HEARTBEAT_PUBLISH_RATE_MS  5000
#define ROS_SPIN_RATE_MS           10

// ============================================================
// GANTRY SPECIFIC PUBLISHERS
// ============================================================
std_msgs::Float32MultiArray encoder_msg_z;
ros::Publisher enc_z_pub("encoder_feedback_z", &encoder_msg_z);

// ============================================================
// DEBUG PUBLISHERS (optional)
// ============================================================
std_msgs::String debug_msg;
ros::Publisher debug_pub("esp32_debug", &debug_msg);
std_msgs::Int32 heartbeat_msg;
ros::Publisher heartbeat_pub("esp32_heartbeat", &heartbeat_msg);

// ============================================================
// SUBSCRIBERS
// ============================================================
void motorCmdZCallback(const std_msgs::Float32MultiArray& msg) {
  if (msg.data_length >= 1) {
    float z_rpm = msg.data[0];
    setMotorZ_RPM(z_rpm);

    Serial.println("");
    Serial.println("╔════════════════════════════════════════╗");
    Serial.println("║    ⚙️  MOTOR COMMAND RECEIVED (Z)     ║");
    Serial.println("╠════════════════════════════════════════╣");
    Serial.printf("║ Z RPM: %-31.2f ║\n", z_rpm);
    Serial.println("╚════════════════════════════════════════╝");
    Serial.println("");
  }
}
ros::Subscriber<std_msgs::Float32MultiArray> motor_z_sub("motor_commands_z", &motorCmdZCallback);

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

// ============================================================
// PUBLISHING FUNCTIONS
// ============================================================
void publishEncoderDataZ() {
  float data[2];   // {z_rpm, z_mm}
  getEncoderZ(data);

  encoder_msg_z.data = data;
  encoder_msg_z.data_length = 2;
  enc_z_pub.publish(&encoder_msg_z);

  Serial.println("");
  Serial.println("╔════════════════════════════════════════╗");
  Serial.println("║       📤 PUBLISHED ENCODER Z          ║");
  Serial.println("╠════════════════════════════════════════╣");
  Serial.printf("║ Z RPM:     %-27.2f ║\n", data[0]);
  Serial.printf("║ Z Position:%-27.2f mm║\n", data[1]);
  Serial.println("╚════════════════════════════════════════╝");
  Serial.println("");
}

// ============================================================
// DEBUG / HEARTBEAT
// ============================================================
unsigned long last_debug_time = 0;
unsigned long last_heartbeat_time = 0;
int heartbeat_counter = 0;

void publishDebugData() {
  unsigned long now = millis();
  if (now - last_debug_time >= DEBUG_PUBLISH_RATE_MS) {
    float data[2];
    getEncoderZ(data);
    char debug_str[100];
    snprintf(debug_str, sizeof(debug_str),
             "ESP32_Z Alive | Z=%.1f RPM | Pos=%.1f mm | HBCount=%d",
             data[0], data[1], heartbeat_counter);
    debug_msg.data = debug_str;
    debug_pub.publish(&debug_msg);
    Serial.printf("[DEBUG Z] %s\n", debug_str);
    last_debug_time = now;
  }
}

void publishHeartbeat() {
  unsigned long now = millis();
  if (now - last_heartbeat_time >= HEARTBEAT_PUBLISH_RATE_MS) {
    heartbeat_msg.data = heartbeat_counter;
    heartbeat_pub.publish(&heartbeat_msg);
    Serial.printf("[HEARTBEAT Z #%d] Published\n", heartbeat_counter);
    heartbeat_counter++;
    last_heartbeat_time = now;
  }
}

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  setupMotorZ();
  Serial.println("\n[INFO] Z Motor Initialized");

  connectWiFi();

  nh.advertise(enc_z_pub);
  nh.advertise(debug_pub);
  nh.advertise(heartbeat_pub);

  nh.subscribe(motor_z_sub);
  nh.subscribe(debug_sub);

  connectROS();
  stopMotorZ();

  Serial.println("\n");
  Serial.println("╔════════════════════════════════════════╗");
  Serial.println("║   ESP32 Z COMMUNICATION READY         ║");
  Serial.println("╠════════════════════════════════════════╣");
  Serial.println("║ PUBLISHING:                           ║");
  Serial.println("║  /encoder_feedback_z (20 Hz)          ║");
  Serial.println("║  /esp32_debug (every 5s)              ║");
  Serial.println("║  /esp32_heartbeat (every 5s)          ║");
  Serial.println("╠════════════════════════════════════════╣");
  Serial.println("║ SUBSCRIBED:                           ║");
  Serial.println("║  /motor_commands_z                    ║");
  Serial.println("║  /esp32_command                       ║");
  Serial.println("╚════════════════════════════════════════╝");
  Serial.println("");
  Serial.println("📡 Waiting for Z commands...");
}

// ============================================================
// LOOP
// ============================================================
unsigned long last_enc_pub = 0;
unsigned long last_spin = 0;

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WARNING] WiFi lost. Reconnecting...");
    connectWiFi();
    connectROS();
  }

  unsigned long now = millis();
  if (now - last_spin >= ROS_SPIN_RATE_MS) {
    nh.spinOnce();
    last_spin = now;
  }

  if (now - last_enc_pub >= ENCODER_PUBLISH_RATE_MS) {
    publishEncoderDataZ();
    last_enc_pub = now;
  }

  publishDebugData();
  publishHeartbeat();
  delay(1);
}