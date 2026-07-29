#ifndef __AD_H
#define __AD_H
#include "sys.h"

void AD_Init(void);
u16 Get_Adc(u8 ch) ;
u16 Get_Adc_Average(u8 ch,u8 times);              								 //湿度百分比转化函数
u16 Get_water(void);
u16 Get_light(void);
uint32_t Get_adc(void);
uint16_t AD_GetValue(uint8_t ADC_Channel);
#endif


