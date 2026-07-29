//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :串口输出温湿度值
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/11/25
//All rights reserved
//******************************************************************************/

#include "sys.h"
#include "Delay.h" 
#include "usart1.h"
#include "usart.h"
#include "LED.h"
#include "DHT11.h"
uint8_t humidity;									//湿度
uint8_t temp;											//温度
char display_buf[48] = {0};		 		//类型转换


int main(void)
{
	Delay_Init();										//延时初始化
	DHT11_Init();										//温湿度初始化
	Usart1_Init(9600);							//串口波特率设置为9600
	Delay_ms(400);									//延时
//	Led_Init();											//LED初始化
	
	while(1)
	{
		DHT11_Read_Data(&temp,&humidity);	  //读取温湿度值
		USART1_SendString("湿度：");
		sprintf(display_buf,"%d",humidity);
		Usart_SendString(USART1,display_buf,2);
		USART1_SendString("\n温度：");
		sprintf(display_buf,"%d",temp);
		Usart_SendString(USART1,display_buf,2);
		Delay_ms(500);
//		GPIO_SetBits(LEDS_GPIO_PORT,LEDS_GPIO_PIN);
//		Delay_ms(500);
//		GPIO_ResetBits(LEDS_GPIO_PORT,LEDS_GPIO_PIN);
//		Delay_ms(500);
	}
}

