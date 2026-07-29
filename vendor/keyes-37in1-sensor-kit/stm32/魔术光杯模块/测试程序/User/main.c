//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :两个灯交替“呼吸”
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/11/25
//All rights reserved
//******************************************************************************/

#include "stm32f10x.h"                  // Device header
#include "Delay.h"
#include "PWM.h"

uint8_t i;

int main(void)
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_12|GPIO_Pin_13;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructure);
	
	
	
	PWM_Init();
	
	while (1)
	{
		if (GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_12) == 0&&GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_13) == 0)
		{
			for (i = 0; i <= 100; i++)
			{
				PWM_SetCompare1(100 - i);
				PWM_SetCompare2(i);
				Delay_ms(10);
			}
			for (i = 0; i <= 100; i++)
			{
				PWM_SetCompare1(i);
				PWM_SetCompare2(100 - i);
				Delay_ms(10);
			}
		}
	}
}
