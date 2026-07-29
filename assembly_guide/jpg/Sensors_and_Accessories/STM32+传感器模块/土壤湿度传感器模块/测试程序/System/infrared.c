#include "infrared.h"

infrared_t InfraredData;
static uint16_t InfraredHightime = 0;

static void InfraredDataInit(void)
{
	InfraredData.ismark = False;
	InfraredData.opcode = 0;
	InfraredData.nopcode = 0;
	InfraredData.sid = 0;
	InfraredData.nsid = 0;
}
void InfraredInit(void)
{
	GPIO_InitTypeDef         GPIO_InitStructure;
	NVIC_InitTypeDef         NVIC_InitStructure;
	EXTI_InitTypeDef         EXTI_InitStructure;
	TIM_TimeBaseInitTypeDef  TIM_TimeBaseStructure;

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOE|RCC_APB2Periph_AFIO, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);
//	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB,ENABLE);
	
	NVIC_InitStructure.NVIC_IRQChannel = EXTI9_5_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);
	
//	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;
//	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
//	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
//	GPIO_Init(GPIOB, &GPIO_InitStructure);
	
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructure);
	
	GPIO_EXTILineConfig(GPIO_PortSourceGPIOE, GPIO_PinSource5);
	EXTI_InitStructure.EXTI_Line = EXTI_Line5;	
	EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
	EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Rising_Falling;
	EXTI_InitStructure.EXTI_LineCmd = ENABLE;
	EXTI_Init(&EXTI_InitStructure);
	
	TIM_TimeBaseStructure.TIM_Period = (5000-1);
	TIM_TimeBaseStructure.TIM_Prescaler = (720-1);//0.01ms   50ms
	TIM_TimeBaseStructure.TIM_ClockDivision = 0;
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
	TIM_TimeBaseStructure.TIM_RepetitionCounter = 0;
	TIM_TimeBaseInit(TIM3, &TIM_TimeBaseStructure);

	TIM_Cmd(TIM3, ENABLE);
	InfraredDataInit();
}

void EXTI9_5_IRQHandler(void)
{
	static uint32_t  irdata = 0;
#if   !Continuous
	static _Bool start = False;
#endif
	if(EXTI_GetITStatus(EXTI_Line5))
	{
		EXTI_ClearITPendingBit(EXTI_Line5);
		if(GPIO_ReadInputDataBit(GPIOE,GPIO_Pin_5))
		{
			/* ??? */
			TIM_SetCounter(TIM3,0);
			InfraredHightime = 0;
		}
		else
		{
			/* ??? */
			InfraredHightime = TIM_GetCounter(TIM3);
			if(InfraredHightime>400 && InfraredHightime<500)
			{
#if   !Continuous				
				start = True;
#endif				
				irdata = 0;
			}
#if   !Continuous
			else if(start)
			{
				if(0)
				{}
#endif
				else if(InfraredHightime>40 && InfraredHightime<72)
				{
					irdata <<= 1;
					irdata |= 0;
				}
				else if(InfraredHightime>150 && InfraredHightime<186)
				{
					irdata <<= 1;
					irdata |= 1;
				}
				else if((InfraredHightime>4000) || (InfraredHightime<220))
				{			
#if   !Continuous
					start = False;
#endif
						InfraredData.sid = irdata>>24;
						InfraredData.nsid = irdata>>16;
						InfraredData.opcode = irdata>>8;
						InfraredData.nopcode = irdata>>0;
						InfraredData.ismark = True;
				}
#if   !Continuous
			}
#endif	
		}
	}
}

