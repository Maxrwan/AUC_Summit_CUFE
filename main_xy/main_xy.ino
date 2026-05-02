// main_xy.ino
#include "motor_xy.h"            // contains setupMotorsXY(), setMotorX_RPM(), setMotorY_RPM(), getEncoderXY()
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
// RATES (adjust as needed)
// ============================================================
#define ENCODER_PUBLISH_RATE_MS    50    // 20 Hz feedback
#define DEBUG_PUBLISH_RATE_MS      5000  // every 5 seconds
#define HEARTBEAT_PUBLISH_RATE_MS  5000
#define ROS_SPIN_RATE_MS           10    // process ROS every 10ms

// ============================================================
// GANTRY SPECIFIC PUBLISHERS
// ============================================================

std_msgs::Float32MultiArray encoder_msg_xy;
ros::Publisher enc_xy_pub("encoder_feedback_xy", &encoder_msg_xy);

// ============================================================
// DEBUG PUBLISHERS (can be removed later)
// ============================================================
std_msgs::String debug_msg;
ros::Publisher debug_pub("esp32_debug", &debug_msg);
std_msgs::Int32 heartbeat_msg;
ros::Publisher heartbeat_pub("esp32_heartbeat", &heartbeat_msg);

// ============================================================
// SUBSCRIBERS
// ============================================================
void motorCmdXYCallback(const std_msgs::Float32MultiArray& msg) {
  if (msg.data_length >= 2) {
    float x_rpm = msg.data[0];
    float y_rpm = msg.data[1];
    setMotorX_RPM(x_rpm);
    setMotorY_RPM(y_rpm);

    Serial.println("");
    Serial.println("╔════════════════════════════════════════╗");
    Serial.println("║    ⚙️  MOTOR COMMAND RECEIVED (XY)    ║");
    Serial.println("╠════════════════════════════════════════╣");
    Serial.printf("║ X RPM: %-31.2f ║\n", x_rpm);
    Serial.printf("║ Y RPM: %-31.2f ║\n", y_rpm);
    Serial.println("╚════════════════════════════════════════╝");
    Serial.println("");
  }
}
ros::Subscriber<std_msgs::Float32MultiArray> motor_xy_sub("motor_commands_xy", &motorCmdXYCallback);

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
void publishEncoderDataXY() {
  float data[4];   // {x_rpm, y_rpm, x_mm, y_mm}
  getEncoderXY(data);

  encoder_msg_xy.data = data;
  encoder_msg_xy.data_length = 4;
  enc_xy_pub.publish(&encoder_msg_xy);

  // Fancy serial output
  Serial.println("");
  Serial.println("╔════════════════════════════════════════╗");
  Serial.println("║       📤 PUBLISHED ENCODER XY         ║");
  Serial.println("╠════════════════════════════════════════╣");
  Serial.printf("║ X RPM:     %-27.2f ║\n", data[0]);
  Serial.printf("║ Y RPM:     %-27.2f ║\n", data[1]);
  Serial.printf("║ X Position:%-27.2f mm║\n", data[2]);
  Serial.printf("║ Y Position:%-27.2f mm║\n", data[3]);
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
    float data[4];
    getEncoderXY(data);
    char debug_str[120];
    snprintf(debug_str, sizeof(debug_str),
             "ESP32_XY Alive | X=%.1f Y=%.1f RPM | Pos (%.1f,%.1f) mm | HBCount=%d",
             data[0], data[1], data[2], data[3], heartbeat_counter);
    debug_msg.data = debug_str;
    debug_pub.publish(&debug_msg);
    Serial.printf("[DEBUG XY] %s\n", debug_str);
    last_debug_time = now;
  }
}

void publishHeartbeat() {
  unsigned long now = millis();
  if (now - last_heartbeat_time >= HEARTBEAT_PUBLISH_RATE_MS) {
    heartbeat_msg.data = heartbeat_counter;
    heartbeat_pub.publish(&heartbeat_msg);
    Serial.printf("[HEARTBEAT XY #%d] Published\n", heartbeat_counter);
    heartbeat_counter++;
    last_heartbeat_time = now;
  }
}

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  setupMotorsXY();
  Serial.println("\n[INFO] XY Motors Initialized");

  connectWiFi();

  // Advertise publishers
  nh.advertise(enc_xy_pub);
  nh.advertise(debug_pub);      // debug
  nh.advertise(heartbeat_pub);  // debug

  // Subscribe to commands
  nh.subscribe(motor_xy_sub);
  nh.subscribe(debug_sub);      // debug

  connectROS();   // also advertises pose_pub & subscribes vel_sub (harmless)
  stopMotorsXY();

  Serial.println("\n");
  Serial.println("╔════════════════════════════════════════╗");
  Serial.println("║   ESP32 XY COMMUNICATION READY        ║");
  Serial.println("╠════════════════════════════════════════╣");
  Serial.println("║ PUBLISHING:                           ║");
  Serial.println("║  /encoder_feedback_xy (20 Hz)         ║");
  Serial.println("║  /esp32_debug (every 5s)              ║");
  Serial.println("║  /esp32_heartbeat (every 5s)          ║");
  Serial.println("╠════════════════════════════════════════╣");
  Serial.println("║ SUBSCRIBED:                           ║");
  Serial.println("║  /motor_commands_xy                   ║");
  Serial.println("║  /esp32_command                       ║");
  Serial.println("╚════════════════════════════════════════╝");
  Serial.println("");
  Serial.println("📡 Waiting for XY commands...");
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
    publishEncoderDataXY();
    last_enc_pub = now;
  }

  publishDebugData();
  publishHeartbeat();
  delay(1);
}