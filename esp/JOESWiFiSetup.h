#ifndef MANGAWIFIROSSETUP_H
#define MANGAWIFIROSSETUP_H

#include <WiFi.h>
#include <WiFiClient.h>
#include <ros.h>
#include <WiFiHardware.h>
#include <geometry_msgs/Pose.h>
#include <geometry_msgs/Pose2D.h>
#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/Twist.h>
#include <nav_msgs/Odometry.h>


// WiFi and ROS Setup
// Static IP Configuration for ESP32
const char* wifi_ssid = "WE_ACFAA2";
const char* wifi_pass = "6988d5ab";
IPAddress ros_server(192, 168, 100, 101);
uint16_t esp_port = 11411;  // Communication port
IPAddress local_IP(192, 168, 100, 58);  // ESP32 IP
IPAddress gateway(192, 168, 1, 1);     // Gateway IP
IPAddress subnet(255, 255, 255, 0);    // Subnet mask

//Ros Handle
extern ros::NodeHandle_<WiFiHardware> nh;

// Declare ROS subscriber for cmd_vel as extern
extern ros::Subscriber<geometry_msgs::Twist> vel_sub;

// Declare Pose2D publisher
extern ros::Publisher pose_pub;         // Publisher for Pose2D
extern geometry_msgs::Pose2D pose_msg;  // Pose2D message

// Function prototypes
void connectWiFi();
void connectROS();
void VelocityCallback(const geometry_msgs::Twist& msg);

// WiFi connection function
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

// ROS connection function
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
#endif // MANGAWIFIROSSETUP_H