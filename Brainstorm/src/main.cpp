#include <Arduino.h>
#include <FastLED.h>

#define LED_PIN 8
#define SENSOR_PIN 7
#define NUM_LEDS 60

CRGB leds[NUM_LEDS];

void setup()
{
  pinMode(SENSOR_PIN, INPUT); // module digital output connected to Arduino pin 8
  Serial.begin(9600);         // initialize serial
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
}

bool is_off(int i)
{
  return (leds[i].r == 0 && leds[i].g == 0 && leds[i].b == 0);
}

void start_lights()
{
  leds[0].setHSV(360 * 0 / NUM_LEDS, 100, 100);
  leds[1].setHSV(360 * 1 / NUM_LEDS, 100, 100);
  leds[2].setHSV(360 * 2 / NUM_LEDS, 100, 100);
  FastLED.show();
}

void update_lights()
{
  leds[NUM_LEDS - 1] = CRGB(0, 0, 0);
  for (int i = NUM_LEDS - 2; i >= 0; i--)
  {
    if (!is_off(i))
    {
      leds[i + 1].setHSV(360 * i / NUM_LEDS, 100, 100);
      leds[i] = CRGB(0, 0, 0);
    }
  }
  FastLED.show();
}

void loop()
{
  int status_sensor = digitalRead(SENSOR_PIN);

  Serial.print(" | Analog pin: ");
  Serial.print(analogRead(A0));
  Serial.print(" | Digital pin: ");

  update_lights();
  if (status_sensor == HIGH)
  {
    Serial.println("High");
    start_lights();
  }
  else
  {
    Serial.println("Low");
  }
  delay(50);
}
