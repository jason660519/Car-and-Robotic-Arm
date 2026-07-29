#include "led.h"
#include "delay.h"
int time_led=0;

/****
*******	LED IO初始化
*****/
void Led_Init(void)
{
	GPIO_InitTypeDef  GPIO_InitStructure;

	RCC_APB2PeriphClockCmd(LEDS_GPIO_CLK,ENABLE);           	//使能端口时钟

	GPIO_InitStructure.GPIO_Pin  = LEDS_GPIO_PIN;  						//引脚配置
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 					//设置成推挽输出
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;		 			//IO口速度为50MHz
 	GPIO_Init(LEDS_GPIO_PORT, &GPIO_InitStructure);						//根据设定参数初始化
	GPIO_SetBits(LEDS_GPIO_PORT,LEDS_GPIO_PIN);  							//IO口输出

}

void Led_reverse(void)
{
    time_led++;												
		Delay_ms(10);
		if(time_led %10 == 0)
			LED_SYS = ~LED_SYS;
		if(time_led >= 5000)
		{
			time_led = 0;
		}
}

