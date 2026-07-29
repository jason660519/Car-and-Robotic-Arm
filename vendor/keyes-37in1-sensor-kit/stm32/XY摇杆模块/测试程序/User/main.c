//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :串口输出VRx，VRy 的值
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/11/25
//All rights reserved
//******************************************************************************/

#include "stm32f10x.h"                  // Device header
#include "Delay.h"
#include "usart1.h"
#include "ADC.h"
 
 
uint16_t ADCXvalue ,ADCYvalue;//创建X，Y变量
char display_buf[48] = {0};		 		//类型转换

int main(void)
{
	
	Delay_Init();										//延时初始化
	Usart1_Init(9600);							//串口波特率设置为9600
	ACD_Init();											//初始化ADC
	Delay_ms(400);									//延时

	while(1)
	{
			ADCXvalue=ADC_Getvalue(ADC_Channel_0);//返回值是通道0
			ADCYvalue=ADC_Getvalue(ADC_Channel_1);//返回值是通道1
		
			USART1_SendString("ADCXvalue:");
			sprintf(display_buf,"%d",ADCXvalue);
			Usart_SendString(USART1,display_buf,4);
			USART1_SendString("\n\r");
			USART1_SendString("ADCYvalue:");
			sprintf(display_buf,"%d",ADCYvalue);
			Usart_SendString(USART1,display_buf,4);
			USART1_SendString("\n\r");
		
			Delay_ms(500);
	}
 
}
	 