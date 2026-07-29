//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :检测磁力控制灯亮灭
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/11/25
//All rights reserved
//******************************************************************************/

#include "sys.h"
#include "Delay.h" 
#include "LED.h"

int main(void)
{
	Delay_Init();										//延时初始化
	Led_Init();											//LED初始化
	
	while(1)
	{
		if(GPIO_ReadInputDataBit(PA,TAP_GPIO)==1)
		{
			GPIO_SetBits(LEDS_GPIO_PORT,LEDS_GPIO_PIN);
			Delay_ms(10);
		}
		else
		{
		GPIO_ResetBits(LEDS_GPIO_PORT,LEDS_GPIO_PIN);
		Delay_ms(500);
		}
	}
}

