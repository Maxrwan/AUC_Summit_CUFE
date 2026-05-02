#ifndef JOESWIFIROSSETUP_H
#define JOESWIFIROSSETUP_H

#include <WiFi.h>
#include <WiFiClient.h>
#include <ros.h>
#include <WiFiHardware.h>
#include <geometry_msgs/Pose.h>
#include <geometry_msgs/Pose2D.h>
#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/Twist.h>
#include <nav_msgs/Odometry.h>
#include <std_msgs/Float32MultiArray.h>
#include <std_msgs/String.h>
#include <std_msgs/Int32.h>

// WiFi and ROS Setup
const char* wifi_ssid = "WE_ACFAA2";
const char* wifi_pass = "6988d5ab";
IPAddress ros_server(192, 168, 122, 1);
uint16_t esp_port = 11411;

// ----- Allow each ESP to define its own IP before including this file -----
#ifndef LOCAL_IP_SET
  #define LOCAL_IP_SET
  IPAddress local_IP(192, 168, 122, 3);   // default, overridable
#endif

IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

// ROS object placeholders (must be defined in main .ino)
extern ros::NodeHandle_<WiFiHardware> nh;
extern ros::Subscriber<geometry_msgs::Twist> vel_sub;
extern ros::Publisher pose_pub;
extern geometry_msgs::Pose2D pose_msg;

void connectWiFi();
void connectROS();
void VelocityCallback(const geometry_msgs::Twist& msg);

void connectWiFi()
{
    Serial.println("[INFO] Setting up Wi-Fi...");
    WiFi.config(local_IP, gateway, subnet);
    WiFi.begin(wifi_ssid, wifi_pass);

    unsigned long to = millis();
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.println("[INFO] Connecting to Wi-Fi...");
        if ((millis() - to) > 5000)
        {
            Serial.println("[ERROR] Failed to connect to Wi-Fi. Restarting...");
            ESP.restart();
        }
    }

    Serial.print("[INFO] Connected to Wi-Fi. IP Address: ");
    Serial.println(WiFi.localIP());
}

void connectROS()
{
    nh.getHardware()->setConnection(ros_server, esp_port);
    nh.initNode();
    nh.subscribe(vel_sub);
    nh.advertise(pose_pub);
    while (!nh.connected())
    {
        nh.spinOnce();
        delay(250);
    }
    Serial.println("[INFO] Connected to ROS master!");
}
#endif