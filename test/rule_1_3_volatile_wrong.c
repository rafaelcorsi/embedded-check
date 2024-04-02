#include "hardware/gpio.h"
#include "pico/stdlib.h"
#include <stdio.h>

const int BTN_PIN_R = 28;
volatile int pressed = 0;
volatile int unpressed = 0;
volatile int foo = 2;

void btn_callback(uint gpio, uint32_t events) {
  if (events == 0x4) { // fall edge
    pressed = 1;
  } else if (events == 0x8) { // rise edge
    unpressed = 1;
  }
}

int main() {
  stdio_init_all();

  gpio_init(BTN_PIN_R);
  gpio_set_dir(BTN_PIN_R, GPIO_IN);
  gpio_pull_up(BTN_PIN_R);

  gpio_set_irq_enabled_with_callback(
      BTN_PIN_R, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true, btn);

  volatile int bar = 3;
  while (true) {
    if (pressed == 1 && foo) {
      printf("fall\n ");
      pressed = 0;
    } else if (unpressed == 1) {
      printf("rise\n ");
      unpressed = 0;
    }
  }
}
