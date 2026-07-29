#ifndef _hwjs_H
#define _hwjs_H

#include "system.h"

//端口定义
#define IRED_PORT 			GPIOA  
#define IRED_PIN 			GPIO_Pin_8
#define IRED_PORT_RCC		RCC_APB2Periph_GPIOA

void Hwjs_Init(void);
u8 HW_jssj(void);

//定义全局变量
extern u32 hw_jsm;
extern u8  hw_jsbz;
extern u8  frame_cnt;

#endif
