//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  文 件 名   : led.c
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241001
//  最近修改   : 
//  功能描述   :led灯配置程序
//  日    期   : 
//  作    者   : 欣薇电子
//  修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/10/1
//All rights reserved
//******************************************************************************/

#include "led.h"
#include "delay.h"
int time_led=0;

/****
*******	LED IO初始化
*****/
void Led_Init(void)
{
	GPIO_InitTypeDef  GPIO_InitStructure;

	RCC_APB2PeriphClockCmd(LEDS_GPIO_CLK,ENABLE);           	//使能端口时钟

	GPIO_InitStructure.GPIO_Pin  = LEDS_GPIO_PIN;  						//引脚配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 					//设置成推挽输出
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;		 			//IO口速度为50MHz
 	GPIO_Init(LEDS_GPIO_PORT, &GPIO_InitStructure);						//根据设定参数初始化
	GPIO_SetBits(LEDS_GPIO_PORT,LEDS_GPIO_PIN);  							//IO口输出

}

void Led_reverse(void)
{
    time_led++;												
		Delay_ms(10);
		if(time_led %10 == 0)
			LED_SYS = ~LED_SYS;
		if(time_led >= 5000)
		{
			time_led = 0;
		}
}

