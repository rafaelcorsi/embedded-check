#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include <time.h>
#include "arq.h"



//************* FUNCOES ****************
void barulho(int freq, int tempo, int pino){
    int periodo = 1000000/freq;
    for(int i = 0; i < tempo*1000/periodo; i++){
        gpio_put(pino, 1);
        sleep_us(periodo/2);
        gpio_put(pino, 0);
        sleep_us(periodo/2);
    }
}
void tocar_musica_tema() {
  

    //fur elise
    // int notas[] = {659, 622, 659, 622, 659, 494, 587, 523, 587, 494, 587, 440, 523, 349, 415, 494, 659, 622, 659, 622, 659, 494, 587, 523, 587, 494, 587, 440, 523, 349, 415, 494, 659, 622, 659, 622, 659, 494, 587, 523, 587, 494, 587, 440, 523, 349, 415, 494, 659, 622, 659, 622, 659, 494, 587, 523, 587, 494, 587, 440, 523, 349, 415, 494};
    // int duracoes[] = {200, 200, 200, 200, 200, 200, 200, 800, 200, 200, 200, 200, 600, 200, 200, 200, 600, 800, 200, 200, 200, 200, 200, 200, 200, 200, 800, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200};

    // Definir as frequências das notas musicais correspondentes à melodia de Harry Potter (uma oitava acima)
    int notas [] = {329, 440, 523, 494, 440, 329, 294, 494, 440, 523, 494, 392, 494, 329, 329, 440, 523, 494};
    int duracoes[] = {300, 300, 300, 300, 300, 300, 600, 300, 300, 600, 300, 300, 600, 300, 300, 300, 300, 300};

    // int notas[] = {329, 440, 523, 494, 440, 329, 294, 494, 440, 523, 494, 392, 494, 329, 329, 440, 523, 494, 440, 329, 392, 370, 349, 277, 349, 329, 329, 329, 523, 440, 523};
    // int duracoes[] = {300, 300, 300, 300, 300, 300, 1000, 300, 300, 300, 300, 300, 300, 1000, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 1000, 300, 300, 1000};
    // int duracoes[] = {300,300,300,300,300,300,600,300,300,300,300,300,600,300,300,300,300,300,300,300,300,300,300,300,300,300,600,300,300,600};
    int num_notas = sizeof(notas) / sizeof(notas[0]);

// Parar se já tiver passado o tempo especificado
        for (int j = 0; j < num_notas ; j++) {
            barulho(notas[j], duracoes[j], buzzer); 
            sleep_ms(100);
        }
        // Mantém o buzzer ligado pelo tempo da nota
         // Desliga o buzzer

         // Breve pausa entre as notas
         
    }



void inicio() {
    tocar_musica_tema(); // Toca a música tema de Harry Potter
    printf("Iniciando o jogo...\n");
}



void buzzer_led(int led_pin) {
    int freq;
    if (led_pin == LED_PIN_RED) {
        freq = 400;
    } else if (led_pin == LED_PIN_GREEN) {
        freq = 500;
    } else if (led_pin == LED_PIN_YELLOW) {
        freq = 600;
    } else {
        freq = 700;
    }

    gpio_put(led_pin, !gpio_get(led_pin));
    barulho(freq, 700, buzzer);
    gpio_put(led_pin, !gpio_get(led_pin));
}


void proximaRodada() {
    const cores[4] = {LED_PIN_BLUE, LED_PIN_GREEN, LED_PIN_RED, LED_PIN_YELLOW}; 
    int sorteio = rand() % 4;
    sequencia[rodada] = cores[sorteio];
    rodada++;
    printf("Rodada: %d\n", rodada);
}

void reproduzirSequencia() {
    for (int i=0; i < rodada; i++) {
        buzzer_led(sequencia[i]);
        sleep_ms(100);
    }
}

void aguardarJogador(){
    for (int i=0; i<rodada; i++) {
        while ((red == 0) && (green == 0) && (blue ==0) && (yellow == 0)) {
            sleep_ms(10);
        }

        if ((red && sequencia[i]==LED_PIN_RED) || 
            (green && sequencia[i]==LED_PIN_GREEN) || 
            (blue && sequencia[i]==LED_PIN_BLUE) || 
            (yellow && sequencia[i]==LED_PIN_YELLOW)) {
            //acertou
            buzzer_led(sequencia[i]);

            red = 0;
            blue = 0;
            green = 0;
            yellow = 0;

        } else {
            //criar efeito luminoso e sonoro para indicar erro
            buzzer_led(LED_PIN_RED);
            buzzer_led(LED_PIN_RED);
            buzzer_led(LED_PIN_RED);
            game_over = 1;
            break;
        }
    }

    sleep_ms(300);
}