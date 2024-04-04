#ifndef ARQ_H
#define ARQ_H

#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include <time.h>

extern int LED_PIN_RED;
extern int LED_PIN_GREEN;
extern int LED_PIN_BLUE;
extern int LED_PIN_YELLOW;

extern int BUTTON_PIN_RED;
extern int BUTTON_PIN_GREEN;
extern int BUTTON_PIN_BLUE;
extern int BUTTON_PIN_YELLOW;
extern int BUTTON_PIN_START;

extern int buzzer;

extern volatile int green;
extern volatile int  red;
extern volatile  int blue;
extern volatile int yellow;
extern volatile int start;

extern volatile int rodada;
extern volatile int sequencia[16];
extern volatile int game_over; 


void barulho(int freq, int tempo, int pino);
void tocar_musica_tema();
void inicio();
void buzzer_led(int led_pin);
void proximaRodada();
void reproduzirSequencia();
void aguardarJogador();

#endif // ARQ_H
