
//  * Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
//  *
//  * SPDX-License-Identifier: BSD-3-Clause
//  */

#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include <time.h>
#include "arq.h"

//****************** VARIAVEIS GLOBAIS ******************

int LED_PIN_RED = 16; //OK
int LED_PIN_GREEN = 17; //OK
int LED_PIN_BLUE = 15;  //OK
int LED_PIN_YELLOW = 14; //ok

int BUTTON_PIN_RED =    12; //ok
int BUTTON_PIN_GREEN =  27; //OK
int BUTTON_PIN_BLUE =   5; //OK
int BUTTON_PIN_YELLOW =18;  //ok
int BUTTON_PIN_START = 19;

int buzzer = 3;


int volatile green = 0;
int volatile red = 0;
int volatile blue = 0;
int volatile yellow = 0;
int volatile start = 0;

int volatile rodada = 0;
int volatile sequencia[16];
int volatile game_over = 0;


//********************* CALLBACKS *********************
void btn_callback(uint gpio, uint32_t events) {
    if (gpio == BUTTON_PIN_START) {
        start = 1;
    }

    if (gpio == BUTTON_PIN_RED) {
        red = 1;
    }
    if (gpio == BUTTON_PIN_GREEN) {
        green = 1;
    }
    if (gpio == BUTTON_PIN_BLUE) {
        blue = 1;
    }
    if (gpio == BUTTON_PIN_YELLOW) {
        yellow = 1;
    }
}
    
int main() {
    stdio_init_all();


    //init dos leds
    gpio_init(LED_PIN_RED);
    gpio_init(LED_PIN_GREEN);
    gpio_init(LED_PIN_BLUE);
    gpio_init(LED_PIN_YELLOW);

    //init dos botoes
    gpio_init(BUTTON_PIN_RED);
    gpio_init(BUTTON_PIN_GREEN);
    gpio_init(BUTTON_PIN_BLUE);
    gpio_init(BUTTON_PIN_YELLOW);

    // set the LED pin to output
    gpio_set_dir(LED_PIN_RED, GPIO_OUT);
    gpio_set_dir(LED_PIN_GREEN, GPIO_OUT);
    gpio_set_dir(LED_PIN_BLUE, GPIO_OUT);
    gpio_set_dir(LED_PIN_YELLOW, GPIO_OUT);

    //botao start
    gpio_set_dir(BUTTON_PIN_START, GPIO_IN);
    gpio_pull_up(BUTTON_PIN_START);
    gpio_set_irq_enabled_with_callback(BUTTON_PIN_START, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true, &btn_callback);

    //botao red
    gpio_set_dir(BUTTON_PIN_RED, GPIO_IN);
    gpio_pull_up(BUTTON_PIN_RED);
    gpio_set_irq_enabled(BUTTON_PIN_RED, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true);
    
    //botao green
    gpio_set_dir(BUTTON_PIN_GREEN, GPIO_IN);
    gpio_pull_up(BUTTON_PIN_GREEN);
    gpio_set_irq_enabled(BUTTON_PIN_GREEN, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true);
   
    //botao blue
    gpio_set_dir(BUTTON_PIN_BLUE, GPIO_IN);
    gpio_pull_up(BUTTON_PIN_BLUE);
    gpio_set_irq_enabled(BUTTON_PIN_BLUE, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true);

    //botao yellow
    gpio_set_dir(BUTTON_PIN_YELLOW, GPIO_IN);
    gpio_pull_up(BUTTON_PIN_YELLOW);
    gpio_set_irq_enabled(BUTTON_PIN_YELLOW, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true);

    gpio_init(buzzer);
    gpio_set_dir(buzzer, GPIO_OUT);

    //iniciar tempo 
    srand(time(NULL));

    inicio();

    while (1) {
        printf("entrou no while: %d\n", start);
        if (start) {
            proximaRodada();
            reproduzirSequencia();
            aguardarJogador();

            // para iniciar um novo jogo
            if (game_over){
                game_over = 0;
                // mostra a pontuacao do jogador
                for (int i = 0; i < rodada - 1 ; i++){
                    buzzer_led(LED_PIN_GREEN);
                    sleep_ms(100);
                }
                start = 0;
                
            }
        }

        if (start == 0){
            rodada = 0;
            red = 0;
            green = 0;
            blue = 0;
            yellow = 0;
            
            
            // buzzer_led(LED_PIN_GREEN);
            // buzzer_led(LED_PIN_BLUE);

    
            // desliga o programa    
        }

        if (rodada == 15){
            //vitoria
            tocar_musica_tema();
            rodada = 0;
            red = 0;
            green = 0;
            blue = 0;
            yellow = 0;
            game_over = 0;
            start = 0;
            sleep_ms(500);
        
        }
            
        }
        
        
}



