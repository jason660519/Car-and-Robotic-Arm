
#ifndef _USART_H_
#define _USART_H_


/**********************************
包含头文件
**********************************/
#include "sys.h"
#include <stdbool.h>
#define LL 200

/**********************************
函数声明
**********************************/

void Usart1_Init(unsigned int baud);			//串口1初始化
void USART1_Clear(void);									//串口1清除缓存
_Bool USART1_WaitRecive(void);						//串口1等待接收完成
void Usart2_Init(unsigned int baud);			//串口2初始化
void USART2_Clear(void);									//串口2清除缓存
_Bool USART2_WaitRecive(void);						//串口2等待接收完成
void Usart_SendString(USART_TypeDef *USARTx, unsigned char *str, unsigned short len);		//发送数据
void UsartPrintf(USART_TypeDef *USARTx, char *fmt,...);		//发送数据

void USART1_SendString(char* str);
void USART_ClearBuffer(void);
bool wifi_SendATCommand(char* cmd, char* response, uint32_t timeout);
unsigned char strsearch(unsigned char*ptr2,unsigned char *ptr1_at);
void resver_data(void);
void UART_Send16Bit(uint16_t data);
void USART1_SendByte(uint8_t Byte);
void USART1_SendArray(uint8_t *Array, uint16_t Length);
uint32_t USART1_Pow(uint32_t X, uint32_t Y);
void USART1_SendNumber(uint32_t Number, uint8_t Length);



void Send_data(void)  ;
#endif
