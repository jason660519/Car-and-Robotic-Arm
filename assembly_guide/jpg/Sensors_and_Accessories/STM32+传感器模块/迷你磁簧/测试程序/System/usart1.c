
/**********************************
包含头文件
**********************************/
//硬件驱动
#include "usart1.h"
#include "delay.h"
#include <stdbool.h>
//C库
#include <stdarg.h>
#include <string.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>


#define BUFFER_SIZE 512
unsigned char buffer[BUFFER_SIZE];
unsigned int usart_flag=0;
volatile int buffer_index = 0;
int finish=1;               //配置完成标志位

uint32_t zz;                //接收模式标志位

char dat;               
char date;                  //接受数据
unsigned int date_flag=1;
extern uint8_t humidity;
/**********************************
变量定义
**********************************/
uint8_t usart1_buf[256];											//串口1接收数组
uint16_t usart1_cnt = 0, usart1_cntPre = 0;
uint8_t usart2_buf[256];											//串口2接收数组
uint16_t usart2_cnt = 0, usart2_cntPre = 0;

/*
************************************************************
*	函数名称：	Usart1_Init
*
*	函数功能：	串口1初始化
*
*	入口参数：	baud：设定的波特率
*
*	返回参数：	无
*
*	说明：			TX-PA9		RX-PA10
************************************************************
*/
void Usart1_Init(unsigned int baud)
{
	GPIO_InitTypeDef gpioInitStruct;
	USART_InitTypeDef usartInitStruct;
	NVIC_InitTypeDef nvicInitStruct;
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);														//GPIOA时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);													//使能USART1时钟
	
	//USART1 PA9	TXD
	gpioInitStruct.GPIO_Mode = GPIO_Mode_AF_PP;																			//复用推挽输出
	gpioInitStruct.GPIO_Pin = GPIO_Pin_9;
	gpioInitStruct.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &gpioInitStruct);
	
	//USART1 PA10	RXD
	gpioInitStruct.GPIO_Mode = GPIO_Mode_IN_FLOATING;																//浮空输入
	gpioInitStruct.GPIO_Pin = GPIO_Pin_10;
	gpioInitStruct.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &gpioInitStruct);
	
	//Usart1 NVIC 配置
	nvicInitStruct.NVIC_IRQChannel = USART1_IRQn;																		//串口1中断
	nvicInitStruct.NVIC_IRQChannelCmd = ENABLE;																			//IRQ通道使能
	nvicInitStruct.NVIC_IRQChannelPreemptionPriority = 0;														//抢占优先级0
	nvicInitStruct.NVIC_IRQChannelSubPriority = 0;																	//子优先级3
	NVIC_Init(&nvicInitStruct);																											//根据指定的参数初始化VIC寄存器
	
	//USART1 初始化设置
	usartInitStruct.USART_BaudRate = baud;																					//串口波特率
	usartInitStruct.USART_HardwareFlowControl = USART_HardwareFlowControl_None;			//无硬件数据流控制
	usartInitStruct.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;											//接收和发送模式
	usartInitStruct.USART_Parity = USART_Parity_No;																	//无奇偶校验位
	usartInitStruct.USART_StopBits = USART_StopBits_1;															//1位停止位
	usartInitStruct.USART_WordLength = USART_WordLength_8b;													//8位数据位
	
	USART_Init(USART1, &usartInitStruct); 																					//初始化串口1
	
	USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);																	//使能接收中断
	
	USART_Cmd(USART1, ENABLE);																											//使能串口
}






// 发送字符串到USART1
void USART1_SendString(char* str) {
    while (*str) {
        USART_SendData(USART1, *str++);
        while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
    }
}



void USART1_IRQHandler(void) {
    if (USART_GetITStatus(USART1, USART_IT_RXNE) != RESET) {
        int receivedChar = USART_ReceiveData(USART1);
			 buffer[buffer_index++] = receivedChar;
        usart_flag=1;
				if(receivedChar == '\r' ||receivedChar == '\n')
				{
					buffer_index =0;
				}
			  if(receivedChar !='\r' && receivedChar !='\n' && receivedChar !=' ' )
				{
				  buffer[buffer_index++] = receivedChar;
				}
				
				if(finish==1)
				{
				  dat= USART_ReceiveData(USART1);
//					resver_data(); 					//接收处理函数
				}					
				else dat=0;
				
				
        if (buffer_index >= 30) {
            buffer_index = 0; // 重置缓冲区索引，避免溢出
        }
    }
}


// 发送AT命令并等待响应
bool wifi_SendATCommand(char* cmd, char* response, uint32_t timeout) {
    while (1) {
			  
        USART_ClearBuffer();
        USART1_SendString(cmd);
				Delay_ms(timeout);
            if (strstr(buffer, response) != NULL) {
                return true;
        }
       
    }
    return false; // 这个返回值永远不会被使用，因为循环一直持续直到成功
}



// 清除USART接收缓冲区
void USART_ClearBuffer(void) {
    memset(buffer, 0, BUFFER_SIZE);
    buffer_index = 0;
}

//本函数是用来检查字符串*ptr2是否完全包含在*ptr1中
//返回:  0  没有找到
//       1-255 从第N个字符开始相同
unsigned char strsearch(unsigned char*ptr2,unsigned char *ptr1_at)//查字符串*ptr2在*ptr1中的位置
{
		unsigned char i=0,j=0,k=0;
		if(ptr2[0]==0) return(0);
		for(i=0,j=0;i<LL;i++)
		{
		if(ptr1_at[i]==ptr2[j])
		{//第一个字符相同
		k=i;
		do {
		if(ptr2[j]=='\0')//比较正确
		return(i+1);               //返回值是整数，不含0
		if(ptr1_at[k]!=ptr2[j]) break;
		k++;j++ ;	 
		} while(k<LL) ;

		j=0;
		}
		}
		return(0);
}



//void resver_data(void)       //接收数据处理函数
//{
//	if(finish==1)
//	{
//	 if(date_flag==1)
//	 {
//			
// 			date_flag=0;
//	  }  
//		if()
//		{
//			date_flag=1;
//			date=dat;
//	  }
// }
//}



void Send_data(void)            //数据发送
{
	USART1_SendString("a");
	USART1_SendNumber(humidity,1);             
	USART1_SendString("b");

}



/*
************************************************************
*	函数名称：	Usart_SendString
*
*	函数功能：	串口数据发送
*
*	入口参数：	USARTx：串口组
*				str：要发送的数据
*				len：数据长度
*
*	返回参数：	无
*
*	说明：		
************************************************************
*/
void Usart_SendString(USART_TypeDef *USARTx, unsigned char *str, unsigned short len)
{
	unsigned short count = 0;
	
	for(; count < len; count++)
	{
		USART_SendData(USARTx, *str++);									//发送数据
		while(USART_GetFlagStatus(USARTx, USART_FLAG_TC) == RESET);		//等待发送完成
	}

}

/*
************************************************************
*	函数名称：	UsartPrintf
*
*	函数功能：	格式化打印
*
*	入口参数：	USARTx：串口组
*				fmt：不定长参
*
*	返回参数：	无
*
*	说明：		
************************************************************
*/
void UsartPrintf(USART_TypeDef *USARTx, char *fmt,...)
{
	unsigned char UsartPrintfBuf[296];
	va_list ap;
	unsigned char *pStr = UsartPrintfBuf;
	
	va_start(ap, fmt);
	vsnprintf((char *)UsartPrintfBuf, sizeof(UsartPrintfBuf), fmt, ap);							//格式化
	va_end(ap);
	
	while(*pStr != 0)
	{
		USART_SendData(USARTx, *pStr++);
		while(USART_GetFlagStatus(USARTx, USART_FLAG_TC) == RESET);
	}
}

/*
************************************************************
*	函数名称：	USART1_Clear
//
*	函数功能：	清空缓存
//
*	入口参数：	无
//
*	返回参数：	无
//
*	说明：		
************************************************************
*/
void USART1_Clear(void)
{
	memset(buffer, 0, sizeof(buffer));
	usart1_cnt = 0;
}

/*
************************************************************
*	函数名称：	UART_Send16Bit
//
*	函数功能：	16进制数发送
//
*	入口参数：	无
//	
************************************************************
*/
void UART_Send16Bit(uint16_t data) {
    while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
    USART_SendData(USART1, (data >> 8) & 0xFF); // 发送高8位

    while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
    USART_SendData(USART1, data & 0xFF); // 发送低8位
}


/**
  * 函    数：串口发送一个字节
  * 参    数：Byte 要发送的一个字节
  * 返 回 值：无
  */
void USART1_SendByte(uint8_t Byte)
{
	USART_SendData(USART1, Byte);		//将字节数据写入数据寄存器，写入后USART自动生成时序波形
	while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);	//等待发送完成
	/*下次写入数据寄存器会自动清除发送完成标志位，故此循环后，无需清除标志位*/
}

/**
  * 函    数：串口发送一个数组
  * 参    数：Array 要发送数组的首地址
  * 参    数：Length 要发送数组的长度
  * 返 回 值：无
  */
void USART1_SendArray(uint8_t *Array, uint16_t Length)
{
	uint16_t i;
	for (i = 0; i < Length; i ++)		//遍历数组
	{
		USART1_SendByte(Array[i]);		//依次调用Serial_SendByte发送每个字节数据
	}
}


/**
  * 函    数：次方函数（内部使用）
  * 返 回 值：返回值等于X的Y次方
  */
uint32_t USART1_Pow(uint32_t X, uint32_t Y)
{
	uint32_t Result = 1;	//设置结果初值为1
	while (Y --)			//执行Y次
	{
		Result *= X;		//将X累乘到结果
	}
	return Result;
}

/**
  * 函    数：串口发送数字
  * 参    数：Number 要发送的数字，范围：0~4294967295
  * 参    数：Length 要发送数字的长度，范围：0~10
  * 返 回 值：无
  */
void USART1_SendNumber(uint32_t Number, uint8_t Length)
{
	uint8_t i;
	for (i = 0; i < Length; i ++)		//根据数字长度遍历数字的每一位
	{
		USART1_SendByte(Number / USART1_Pow(10, Length - i - 1) % 10 + '0');	//依次调用Serial_SendByte发送每位数字
	}
}

/*
************************************************************
*	函数名称：	USART2_IRQHandler
*
*	函数功能：	串口2收发中断
*
*	入口参数：	无
*
*	返回参数：	无
*
*	说明：		
************************************************************
*/
void USART2_IRQHandler(void)
{
	if(USART_GetITStatus(USART2, USART_IT_RXNE) != RESET) 		//接收中断
	{
		if(usart2_cnt >= sizeof(usart2_buf))	usart2_cnt = 0; 	//防止串口被刷爆
		usart2_buf[usart2_cnt++] = USART2->DR;
		
		USART_ClearFlag(USART2, USART_FLAG_RXNE);
	}
}


//加入以下代码,支持printf函数,而不需要选择use MicroLIB	  
#if 1
#pragma import(__use_no_semihosting)             
//标准库需要的支持函数                 
struct __FILE 
{ 
	int handle; 

}; 

FILE __stdout;       
//定义_sys_exit()以避免使用半主机模式    
void _sys_exit(int x) 
{ 
	x = x; 
} 
//重定义fputc函数 
int fputc(int ch, FILE *f)
{      
	while((USART1->SR&0X40)==0){;}//循环发送,直到发送完毕   
    USART1->DR = (u8) ch;      
	return ch;
}
#endif 

