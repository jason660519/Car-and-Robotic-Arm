//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :串口输出时间
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/11/25
//All rights reserved
//******************************************************************************/


#include "stm32f10x.h"
#include <stdio.h>
#include <string.h>
 
#define AHB_INPUT 72
 
#define DS1302_PORT           GPIOB
#define DS1302_SCK_PIN        GPIO_Pin_5
#define DS1302_IO_PIN         GPIO_Pin_6
#define DS1302_CE_PIN         GPIO_Pin_7
 
u8 WRITE_RTC_ADDR[7] = {0x80, 0x82, 0x84, 0x86, 0x88, 0x8a, 0x8c};
u8 TIME[7] = {0, 0x30, 0x17, 0x02, 0x05, 0x01, 0x19};
 
void delay_us(uint32_t time_us)
{
	SysTick->LOAD = AHB_INPUT * time_us;
	SysTick->VAL = 0x00;
	SysTick->CTRL = 0x00000005;
	for(;!(SysTick->CTRL & 0x00010000););
	SysTick->CTRL = 0x00000004;
}
 
void delay_ms(uint32_t time_ms)
{
	for(;time_ms-- > 0;)
	{
		delay_us(1000);
	}
}
 
void usart1_init(uint32_t bound)
{
	GPIO_InitTypeDef GPIO_InitStructure;
	USART_InitTypeDef USART_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;
	
	RCC_APB2PeriphClockCmd(RCC_APB1Periph_USART2 | RCC_APB2Periph_GPIOA, ENABLE);
	
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_Init(GPIOA, &GPIO_InitStructure);
	
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIO_Init(GPIOA, &GPIO_InitStructure);
	
	NVIC_InitStructure.NVIC_IRQChannel = USART2_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 3;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 3;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);
	
	USART_InitStructure.USART_BaudRate = bound;
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;
	USART_InitStructure.USART_StopBits = USART_StopBits_1;
	USART_InitStructure.USART_Parity = USART_Parity_No;
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_Init(USART2, &USART_InitStructure);
	USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
	USART_Cmd(USART2, ENABLE);
	
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz; 
	GPIO_Init(GPIOA, &GPIO_InitStructure);
	GPIO_ResetBits(GPIOA, GPIO_Pin_1);
}
 
void RCC_Configuration(void)
{
	RCC_DeInit();
	RCC_HSEConfig(RCC_HSE_ON);
	while(RCC_GetFlagStatus(RCC_FLAG_HSERDY) == RESET);
	
	FLASH_PrefetchBufferCmd(FLASH_PrefetchBuffer_Enable);	//Enable Prefetch Buffer
	FLASH_SetLatency(FLASH_Latency_2);		//Flash 2 wait state
	
	RCC_HCLKConfig(RCC_SYSCLK_Div1);		//HCLK = SYSCLK
	RCC_PCLK2Config(RCC_HCLK_Div1);			//PCLK2 =  HCLK
	RCC_PCLK1Config(RCC_HCLK_Div2);			//PCLK1 = HCLK/2
	RCC_PLLConfig(RCC_PLLSource_HSE_Div1,RCC_PLLMul_9);	//PLLCLK = 8MHZ * 9 =72MHZ
	RCC_PLLCmd(ENABLE);			//Enable PLLCLK
	
	while(RCC_GetFlagStatus(RCC_FLAG_PLLRDY) == RESET){};
	
  RCC_SYSCLKConfig(RCC_SYSCLKSource_PLLCLK);	//Select PLL as system clock
	while(RCC_GetSYSCLKSource()!=0x08);		//Wait till PLL is used as system clock source
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE); 
}
 
void RS485_Config(u32 bound)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    USART_InitTypeDef USART_InitStructure;
    NVIC_InitTypeDef NVIC_InitStructure;
    
    /* config USART1 clock */
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2 , ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA  , ENABLE);
    
    /* USART1 GPIO config */
    /* Configure USART1 Tx (PA.02) as alternate function push-pull *///TX
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    /* Configure USART1 Rx (PA.03) as input floating *///RX
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    
    
    USART_InitStructure.USART_BaudRate = bound;
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;
    USART_InitStructure.USART_StopBits = USART_StopBits_1;
    USART_InitStructure.USART_Parity = USART_Parity_No ;
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART2, &USART_InitStructure);
    
    
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 3;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 2;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
    
    USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
    USART_Cmd(USART2, ENABLE);
    
    //USART_ClearFlag(USART1, USART_FLAG_TC);
 
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1; 
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz; 
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    GPIO_SetBits(GPIOA, GPIO_Pin_1);
    
}
 
void func_ds1302_configuration()
{
	GPIO_InitTypeDef GPIO_InitStruct; 
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	
	GPIO_InitStruct.GPIO_Pin = DS1302_SCK_PIN | DS1302_CE_PIN ;  
	GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP;
	GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(DS1302_PORT, &GPIO_InitStruct);  
 
}
 
void func_config_ds1302_io_pin(u8 in_out)
{
	GPIO_InitTypeDef GPIO_InitStruct;
	if(in_out == 1)
	{
		GPIO_InitStruct.GPIO_Pin = DS1302_IO_PIN;
		GPIO_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP;
		GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
		GPIO_Init(DS1302_PORT, &GPIO_InitStruct);
	}
	else
	{
		GPIO_InitStruct.GPIO_Pin = DS1302_IO_PIN;
		GPIO_InitStruct.GPIO_Mode = GPIO_Mode_IPU;
		GPIO_Init(DS1302_PORT, &GPIO_InitStruct);
	}
}
 
void nop(u8 nop_cnt)
{
	for(;nop_cnt-- > 0;)
	{
		__NOP();
	}
}
 
 
void func_write_ds1302_a_byte(u8 addr, u8 dat)
{
	u8 n;
	
	GPIO_ResetBits(DS1302_PORT, DS1302_CE_PIN);
	nop(2);
	GPIO_ResetBits(DS1302_PORT, DS1302_SCK_PIN);
	nop(2);
	GPIO_SetBits(DS1302_PORT, DS1302_CE_PIN);
	nop(2);
	func_config_ds1302_io_pin(1);
	nop(2);
	
	for (n=0; n<8; n++)
	{
		GPIO_WriteBit(DS1302_PORT, DS1302_IO_PIN, (BitAction)(0x01 & addr));
		addr >>= 1;
		GPIO_SetBits(DS1302_PORT, DS1302_SCK_PIN);
		nop(2);
		GPIO_ResetBits(DS1302_PORT, DS1302_SCK_PIN);
		nop(2);
	}
	for (n=0; n<8; n++)
	{
		GPIO_WriteBit(DS1302_PORT, DS1302_IO_PIN, (BitAction)(0x01 & dat));
		dat >>= 1;
		GPIO_SetBits(DS1302_PORT, DS1302_SCK_PIN);
		nop(2);
		GPIO_ResetBits(DS1302_PORT, DS1302_SCK_PIN);
		nop(2);   
	}   
			 
	GPIO_ResetBits(DS1302_PORT, DS1302_CE_PIN);
	nop(2); 
}
 
/**
* CLOCK - SEC : 0x81
* CLOCK - MIN : 0x83
* CLOCK - HR : 0x85
* CLOCK - DATE : 0x87
* CLOCK - MONTH : 0x89
* CLOCK - DAY : 0x8B
* CLOCK - YEAR : 0x8D
*/
u8 func_read_ds1302_a_byte(u8 cmd)
{
	u8 tmp;
	u8 i;
	u8 ret;
	
	if(cmd < 0x81 || cmd > 0x8F)
	{
		return 255;
	}
	
	GPIO_ResetBits(DS1302_PORT, DS1302_CE_PIN);
	GPIO_ResetBits(DS1302_PORT, DS1302_SCK_PIN);
	func_config_ds1302_io_pin(1);
	nop(5);
	GPIO_SetBits(DS1302_PORT, DS1302_CE_PIN);
	for(i = 0; i < 8; i++)
	{
		tmp = cmd;
		tmp= tmp >> i;
		GPIO_WriteBit(DS1302_PORT, DS1302_IO_PIN, (BitAction)(0x01 & tmp));
		nop(2);
		GPIO_SetBits(DS1302_PORT, DS1302_SCK_PIN);
		nop(2);
		GPIO_ResetBits(DS1302_PORT, DS1302_SCK_PIN);
		nop(2);
	}
	
	func_config_ds1302_io_pin(0);
	nop(2);
	for(i = 0; i < 8; i++)
	{
		tmp = GPIO_ReadInputDataBit(DS1302_PORT, DS1302_IO_PIN);
		ret = ret | (tmp << i);
		GPIO_SetBits(DS1302_PORT, DS1302_SCK_PIN);
		nop(2);
		GPIO_ResetBits(DS1302_PORT, DS1302_SCK_PIN);
		nop(2);
	}
	GPIO_ResetBits(DS1302_PORT, DS1302_CE_PIN);
	nop(2);
	func_config_ds1302_io_pin(1);
	nop(2);
	GPIO_SetBits(DS1302_PORT, DS1302_SCK_PIN);
	nop(2);
	GPIO_ResetBits(DS1302_PORT, DS1302_IO_PIN);
	nop(2);
	GPIO_SetBits(DS1302_PORT, DS1302_IO_PIN);
	nop(2);
	return ret;
}
 
u8 func_read_ds1302_time(char *ret_time)
{
	u8 ret;
	u8 tmp_t[14];
	
	//YEAR
	ret = func_read_ds1302_a_byte(0x8D);
	if(ret == 255)
	{
		return 255;
	}
	tmp_t[1] = ret & 0x0f;
	tmp_t[0] = ret >> 4;
	
	//MONTH
	ret = func_read_ds1302_a_byte(0x89);
	if(ret == 255)
	{
		return 255;
	}
	tmp_t[3] = ret & 0x0f;
	tmp_t[2] = ret >> 4;
	
	//DATE
	ret = func_read_ds1302_a_byte(0x87);
	if(ret == 255)
	{
		return 255;
	}
	tmp_t[5] = ret & 0x0f;
	tmp_t[4] = ret >> 4;
	
	//HR
	ret = func_read_ds1302_a_byte(0x85);
	if(ret == 255)
	{
		return 255;
	}
	tmp_t[7] = ret & 0x0f;
	tmp_t[6] = ret >> 4;
	
	//MIN
	ret = func_read_ds1302_a_byte(0x83);
	if(ret == 255)
	{
		return 255;
	}
	tmp_t[9] = ret & 0x0f;
	tmp_t[8] = ret >> 4;
	
	//SEC
	ret = func_read_ds1302_a_byte(0x81);
	if(ret == 255)
	{
		return 255;
	}
	tmp_t[11] = ret & 0x0f;
	tmp_t[10] = ret >> 4;	
	
	sprintf(ret_time, "20%d%d-%d%d-%d%d %d%d:%d%d:%d%d ", tmp_t[0], tmp_t[1], tmp_t[2], tmp_t[3], tmp_t[4], tmp_t[5], tmp_t[6], tmp_t[7], tmp_t[8], tmp_t[9], tmp_t[10], tmp_t[11]);
	return 0;
}
 
 
void Ds1302Init()
{
	
	u8 n;
	func_write_ds1302_a_byte(0x8E, 0X00);
	for (n=0; n<7; n++)
	{
		 func_write_ds1302_a_byte(WRITE_RTC_ADDR[n], TIME[n]); 
	}
	
	func_write_ds1302_a_byte(0x8E,0x80);
}
 
int main()
{	
	
	u8 i = 0;
	u8 suc;
	char ch_t[24];
	
	RS485_Config(9600);
	
	func_ds1302_configuration();
	
	Ds1302Init();
	
	while (1)
	{
		suc = func_read_ds1302_time(ch_t);
		if(suc == 0)
		{
			for(i = 0; i < 20; i++)
			{
				USART_SendData(USART2, ch_t[i]);
				while(USART_GetFlagStatus(USART2, USART_FLAG_TC) == RESET);
			}
		}
		
		delay_ms(1000);
	}
}