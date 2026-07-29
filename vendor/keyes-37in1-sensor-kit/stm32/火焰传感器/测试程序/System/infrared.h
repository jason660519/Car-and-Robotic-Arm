#ifndef   __INFRARED_H
#define   __INFRARED_H

#include "stm32f10x.h"

#define   False    0
#define   True     1

#define   Continuous    False

typedef struct
{
	uint8_t sid;//System identification code
	uint8_t nsid;//System identification code inverse code
	uint8_t opcode;//operation code
	uint8_t nopcode;//operation code inverse code
	_Bool ismark;//Infrared switching mark
}infrared_t;

extern infrared_t InfraredData;

void InfraredInit(void);

#endif
