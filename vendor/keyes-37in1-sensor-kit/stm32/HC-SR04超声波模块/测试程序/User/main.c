//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :串口输出模块与物体之间的距离
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
#include "Timer.h"
#include "HCSR04.h"
 
char display_buf[48] = {0};		 		//类型转换

int main(void)
{
	
	Delay_Init();										//延时初始化
	Usart1_Init(9600);							//串口波特率设置为9600
  Timer_Init();  							  //初始化定时器
  HC_SR04_Init();    						//初始化超声波测距模块
	Delay_ms(400);									//延时

	while(1)
	{
			int Distance_mm=sonar_mm();
			Delay_ms(500);
			USART1_SendString("\r\n");
			USART1_SendString("Distance(mm):");
			sprintf(display_buf,"%d",Distance_mm);
			Usart_SendString(USART1,display_buf,4);

	}
 
}
	 