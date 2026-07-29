//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :串口输出温度值
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
#include "ds18b20.h"
char display_buf[48] = {0};		 		//类型转换


int main(void)
{
	Delay_Init();										//延时初始化
	Usart1_Init(9600);							//串口波特率设置为9600
	DS18B20_Init();//DS18B20初始化
	Delay_ms(400);									//延时
	
	
	while(1)
	{
		temperature=DS18B20_Get_Temp();
		Delay_ms(1000);
		USART1_SendString("\n温度：");
		sprintf(display_buf,"%d",temperature);
		Usart_SendString(USART1,display_buf,2);
		USART1_SendString("\n\r");
//		Delay_ms(1000);

	}
}

