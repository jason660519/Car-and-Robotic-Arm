#ifndef __BEEP_H
#define __BEEP_H
#include "sys.h"  
#include "stm32f10x.h"                  // Device header

#define BEEP PAout(11)  

void BEEP_Init(void);         
void Sound(u16 frq);
void Sound2(u16 time);
void play_music(void);
void play_successful(void);
void play_failed(void);

#endif
