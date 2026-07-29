//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :RGB灯呈现不同颜色
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/11/25
//All rights reserved
//******************************************************************************/

#include "stm32f10x.h"                  // Device header
#include "Delay.h"
#include "RGB.h"
uint8_t i;
int main(void)
{
 
	RGB_Init();
	while (1)
	{	
			for(i=0;i<255;i++)
			{
				LED_SetRGB(220*i/250,20*i/250,60*i/250);	//呼吸灯
				Delay_ms(10);
			}
			for(i=255;i>0;i--)
			{
				LED_SetRGB(220*i/250,20*i/250,60*i/250);												
				Delay_ms(10);
			}
			LED_SetRGB(255,0,0);//红色
			Delay_ms(1000);
		
			LED_SetRGB(0,255,0);//绿色
			Delay_ms(1000);
		
			LED_SetRGB(0,0,255);//蓝色
			Delay_ms(1000);
		
			LED_SetRGB(255,255,0);//黄色
			Delay_ms(1000);
		
			LED_SetRGB(0,255,255);//青色
			Delay_ms(1000);
		
			LED_SetRGB(255,0,255);//紫红色
			Delay_ms(1000);
		
			LED_SetRGB(192,192,192);//银
			Delay_ms(1000);
		
			LED_SetRGB(128,128,128);//灰色
			Delay_ms(1000);
		
			LED_SetRGB(128,0,0);//	栗色
			Delay_ms(1000);
		
			LED_SetRGB(128,128,0);//橄榄色
			Delay_ms(1000);
			
			LED_SetRGB(0,128,0);//绿色
			Delay_ms(1000);
			
			LED_SetRGB(128,0,128);//紫色
			Delay_ms(1000);
			
			LED_SetRGB(0,128,128);//蓝绿色
			Delay_ms(1000);
			
			LED_SetRGB(0,0,128);//海军色
			Delay_ms(1000);
			
			LED_SetRGB(0,0,0);
			Delay_ms(1000);
			
			LED_SetRGB(255,255,255);
			Delay_ms(1000);
		
		
	}
}

