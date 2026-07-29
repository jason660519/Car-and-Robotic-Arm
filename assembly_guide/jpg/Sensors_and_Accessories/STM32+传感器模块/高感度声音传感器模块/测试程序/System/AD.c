//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  文 件 名   : ad.c
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241001
//  最近修改   : 
//  功能描述   : adc配置
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/10/1
//All rights reserved
//******************************************************************************/
#include "delay.h"
#include "ad.h" 
uint32_t M_max=3250;           //干燥时数值
uint32_t M_min=1450;           //湿润时数值

uint32_t Current_m=0;           //当前湿度百分比
uint32_t AD=0;               	  //AD值
uint32_t temp=0;             	  //AD取平均暂存
int i=0;                        //转换计数
/**
  * 函    数：AD初始化
  * 参    数：无
  * 返 回 值：无
  */
void AD_Init(void)
{
	/*开启时钟*/
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE);	//开启ADC1的时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);	//开启GPIOA的时钟
	
	/*设置ADC时钟*/
	RCC_ADCCLKConfig(RCC_PCLK2_Div6);						//选择时钟6分频，ADCCLK = 72MHz / 6 = 12MHz
	
	/*GPIO初始化*/
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0 |GPIO_Pin_1 ;         //通道8 通道9
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructure);					//将引脚初始化为模拟输入
	
	/*不在此处配置规则组序列，而是在每次AD转换前配置，这样可以灵活更改AD转换的通道*/
	
	/*ADC初始化*/
	ADC_InitTypeDef ADC_InitStructure;						//定义结构体变量
	ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;		//模式，选择独立模式，即单独使用ADC1
	ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;	//数据对齐，选择右对齐
	ADC_InitStructure.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;	//外部触发，使用软件触发，不需要外部触发
	ADC_InitStructure.ADC_ContinuousConvMode = DISABLE;		//连续转换，失能，每转换一次规则组序列后停止
	ADC_InitStructure.ADC_ScanConvMode = DISABLE;			//扫描模式，失能，只转换规则组的序列1这一个位置
	ADC_InitStructure.ADC_NbrOfChannel = 1;					//通道数，为1，仅在扫描模式下，才需要指定大于1的数，在非扫描模式下，只能是1
	ADC_Init(ADC1, &ADC_InitStructure);						//将结构体变量交给ADC_Init，配置ADC1
	
	/*ADC使能*/
	ADC_Cmd(ADC1, ENABLE);									//使能ADC1，ADC开始运行
	
	/*ADC校准*/
	ADC_ResetCalibration(ADC1);								//固定流程，内部有电路会自动执行校准
	while (ADC_GetResetCalibrationStatus(ADC1) == SET);
	ADC_StartCalibration(ADC1);
	while (ADC_GetCalibrationStatus(ADC1) == SET);
}

/**
  * 函    数：获取AD转换的值
  * 参    数：ADC_Channel 指定AD转换的通道，范围：ADC_Channel_x，其中x可以是0/1/2/3
  * 返 回 值：AD转换的值，范围：0~4095
  */
//获得ADC值
//ch:通道值 0~3
u16 Get_Adc(u8 ch)   
{
  	//设置指定ADC的规则组通道，一个序列，采样时间
	ADC_RegularChannelConfig(ADC1, ch, 1, ADC_SampleTime_239Cycles5 );	//ADC1,ADC通道,采样时间为239.5周期	  			    
  
	ADC_SoftwareStartConvCmd(ADC1, ENABLE);		//使能指定的ADC1的软件转换启动功能	
	 
	while(!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC ));//等待转换结束

	return ADC_GetConversionValue(ADC1);	//返回最近一次ADC1规则组的转换结果
}

u16 Get_Adc_Average(u8 ch,u8 times)    //获取平均值
{
	u32 temp_val=0;
	u8 t;
	for(t=0;t<times;t++)
	{
		temp_val+=Get_Adc(ch);
		Delay_ms(5);
	}
	return temp_val/times;
} 	 

u16 Get_water(void)
{
	u16 aa=0;
  aa = Get_Adc_Average(9,30);			//选择通道1
	
	if(aa>M_max)  aa=M_max;         //限幅
	if(aa<M_min)  aa=M_min;
	aa=(aa-M_min)*100/(M_max-M_min);  //转化位百分数
	return aa; 
}


//  1280   4095
u16 Get_light(void)
{
	u16 bb=0;
  bb = Get_Adc_Average(8,30);		//选择通道0
	
	if(bb>4090)  bb=4090;         //限幅
	if(bb<1280)  bb=1280;
	bb=(4200-bb)*100/(4200-1280);  //转化位百分数
	if(bb==100) bb=99;
	return bb; 
}


uint32_t Get_adc(void)               								//湿度百分比转化函数
{			
	for(i=0;i<=50;i++)                							  //累加50次
	{
  	AD=AD_GetValue(ADC_Channel_9);   						  	//采集AD值
//		Delay_ms(100);			//延时100ms，手动增加一些转换的间隔时间
		temp=AD+temp;
		AD=0;
	}
	temp=temp/50;                                     //取平均值
	if(temp>M_max)  temp=M_max;                       //最大限幅
	if(temp<M_min)  temp=M_min;												//最小限幅
	Current_m=(M_max-temp)*100/(M_max-M_min);         //转化为百分数
	return Current_m;                                 //函数返回转化值
}

uint16_t AD_GetValue(uint8_t ADC_Channel)
{
	ADC_RegularChannelConfig(ADC1, ADC_Channel, 1, ADC_SampleTime_55Cycles5);	//在每次转换前，根据函数形参灵活更改规则组的通道1
	ADC_SoftwareStartConvCmd(ADC1, ENABLE);																		//软件触发AD转换一次
	while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);										//等待EOC标志位，即等待AD转换结束
	return ADC_GetConversionValue(ADC1);																			//读数据寄存器，得到AD转换的结果
}
