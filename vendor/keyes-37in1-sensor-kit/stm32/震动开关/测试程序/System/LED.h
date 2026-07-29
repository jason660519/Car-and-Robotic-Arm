#ifndef __LED_H
#define __LED_H


/**********************************
包含头文件
**********************************/
#include "sys.h"


/**********************************
重定义关键词
**********************************/
#define LEDS_GPIO_CLK                 RCC_APB2Periph_GPIOC        //最小系统LED
#define LEDS_GPIO_PORT                GPIOC

#define PA     												GPIOA
#define TAP_GPIO											GPIO_Pin_15
#define TAP														PAin(15)

#define LEDS_GPIO_PIN                 GPIO_Pin_13
#define LED_SYS                       PCout(13)

//#define LED_red                        GPIO_Pin_14
//#define LED_go                         PCout(14)	

//#define LED_green                         GPIO_Pin_15
//#define LED_back                          PCout(15)	

/**********************************
函数声明
**********************************/
void Led_Init(void);													//GPIO初始化
void Led_reverse(void);	

#endif
