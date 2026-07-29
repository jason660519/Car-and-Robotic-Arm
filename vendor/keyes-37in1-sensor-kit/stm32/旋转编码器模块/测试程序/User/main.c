//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :串口输出编码器旋转值
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
#include "TIM.h"

int main(void)
{
	Delay_Init();										//延时初始化
	Encoder_Init();
	Usart1_Init(9600);							//串口波特率设置为9600
	Delay_ms(400);									//延时
	int16_t temp=0;
	
	while(1)
	{
		if(temp!=Encoder_Get())
		{	
			
				temp=Encoder_Get();
				USART1_SendString("数据：");
				USART1_SendNumber(temp,3);
				USART1_SendString("\n");
				Delay_ms(20);
			
		}
		Delay_ms(80);
	}
}

