# Brainstorm

This is a prototype for GLOW 2025. It uses a KY-038 sound sensor to detect clapping and a LED (WS2812) strip to display the light flowing from the sensor outwards.

# Pin Layout

| **Component**    | **Pin**          | **Connected To (Arduino)** |
| ---------------- | ---------------- | -------------------------- |
| **KY-038**       | +                | 3.3V                       |
|                  | G                | GND                        |
|                  | AO (Analog Out)  | A0                         |
|                  | DO (Digital Out) | D7                         |
| **WS2812 Strip** | DIN (Data In)    | D8                         |
|                  | VCC              | 5V                         |
|                  | GND              | GND                        |

[![preview](https://github.com/BRISINGR-01/Fontys-projects/blob/main/Brainstorm/assets/video-preview.jpg)](https://github.com/BRISINGR-01/Fontys-projects/blob/main/Brainstorm/assets/20250515_155512.mp4)

![hardware](https://github.com/BRISINGR-01/Fontys-projects/blob/main/Brainstorm/assets/20250515_155706.jpg)
