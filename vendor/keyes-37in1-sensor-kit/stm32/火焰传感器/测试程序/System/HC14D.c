#include "stm32f10x.h"                  // Device header
#include "Delay.h" 
#include "usart.h" 
void HC140_Config(void)
{
   RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	GPIO_InitTypeDef GPIO_InitStructure = {0};//定义一个结构体变量 
			
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0; //PA0
	GPIO_InitStructure.GPIO_Mode =  GPIO_Mode_IN_FLOATING; //浮空输入
	GPIO_Init(GPIOB, &GPIO_InitStructure); //初始化结构体
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC,ENABLE);
    GPIO_InitTypeDef fengmingqi;
    fengmingqi.GPIO_Mode=GPIO_Mode_Out_PP;
    fengmingqi.GPIO_Pin=GPIO_Pin_14;
    fengmingqi.GPIO_Speed=GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &fengmingqi);
	
	
}

void HC140_GET(void)
{
	if(GPIO_ReadInputDataBit(GPIOA,GPIO_Pin_0)!=1)
	{
		printf("触发\r\n");
		GPIO_SetBits(GPIOC,GPIO_Pin_14);
	}
}

