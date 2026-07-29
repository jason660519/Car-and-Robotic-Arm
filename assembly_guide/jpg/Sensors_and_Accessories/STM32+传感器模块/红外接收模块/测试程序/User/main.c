//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :串口输出模块接收到的红外接收码
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/11/25
//All rights reserved
//******************************************************************************/

#include "system.h"
#include "SysTick.h"
#include "led.h"
#include "usart.h"
#include "hwjs.h"
#include "smg.h"


int main()
{
//	u8 i=0;
	u8 buf[3];
	u8 data_code=0;
	
	SysTick_Init(72);
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);  //中断优先级分组分2组
	USART1_Init(115200);
	LED_Init();
//	SMG_Init();
	Hwjs_Init();
	
	while(1)
	{	
		if(hw_jsbz==1)	//如果红外接收到
		{
			hw_jsbz=0;	   //清零
			printf("红外接收码 %0.8X\r\n",hw_jsm);	//打印
			data_code=hw_jsm>>8;
			hw_jsm=0;					//接收码清零
		}	
		buf[0]=gsmg_code[data_code/16];
		buf[1]=gsmg_code[data_code%16];
		buf[2]=0X76;
		SMG_Display(buf,6);
		
//		i++;
//		if(i%10==0)
//			LED0=!LED0;

		delay_ms(10);
	}
}
