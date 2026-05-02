#include "MotorXY.h"           // your motor_xy.h / motor_xy.cpp (separate file for XY)
#include "WiFiHardware.h"
#define LOCAL_IP_SET
IPAddress local_IP(192, 168, 100, 58);   // IP for ESP32_XY
#include "JOESWiFiSetup.h"

// ----- Required by JOESWiFiSetup -----
ros::NodeHandle_<WiFiHardware> nh;

void dummyVelCallback(const geometry_msgs::Twist& msg) {
  // not used in this application
}
ros::Subscriber<geometry_msgs::Twist> vel_sub("cmd_vel", &dummyVelCallback);

geometry_msgs::Pose2D pose_msg;
ros::Publisher pose_pub("robot_pose", &pose_msg);

// ----- Gantry specific topics -----
#include <std_msgs/Float32MultiArray.h>

std_msgs::Float32MultiArray encoder_msg_xy;
ros::Publisher enc_xy_pub("encoder_feedback_xy", &encoder_msg_xy);

void motorCmdXYCallback(const std_msgs::Float32MultiArray& msg) {
  if (msg.data_length >= 2) {
    setMotorX_RPM(msg.data[0]);
    setMotorY_RPM(msg.data[1]);
    Serial.printf("[CMD XY] X=%.2f Y=%.2f RPM\n", msg.data[0], msg.data[1]);
  }
}
ros::Subscriber<std_msgs::Float32MultiArray> motor_xy_sub("motor_commands_xy", &motorCmdXYCallback);

// Timing
unsigned long lastEncPub = 0;
const unsigned long ENC_PUB_MS = 50;   // 20 Hz

void setup() {
  Serial.begin(115200);
  setupMotorsXY();
  connectWiFi();

  nh.advertise(enc_xy_pub);
  nh.subscribe(motor_xy_sub);

  connectROS();   // this also advertises pose_pub and subscribes vel_sub (harmless)
  stopMotorsXY();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    connectROS();
  }
  nh.spinOnce();

  unsigned long now = millis();
  if (now - lastEncPub >= ENC_PUB_MS) {
    float data[4];
    getEncoderXY(data);          // fills {x_rpm, y_rpm, x_pos_mm, y_pos_mm}
    encoder_msg_xy.data = data;
    encoder_msg_xy.data_length = 4;
    enc_xy_pub.publish(&encoder_msg_xy);
    lastEncPub = now;
  }
  delay(1);
}