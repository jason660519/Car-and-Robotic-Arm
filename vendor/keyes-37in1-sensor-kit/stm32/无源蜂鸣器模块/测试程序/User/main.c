//////////////////////////////////////////////////////////////////////////////////	 
//本程序只供学习使用，未经作者许可，不得用于其它任何用途
//欣薇电子
//
//  版 本 号   : v1.0
//  作    者   : 欣薇电子
//  生成日期   : 20241125
//  最近修改   : 
//  功能描述   :蜂鸣器播放歌曲音调
// 日    期   : 
// 作    者   : 欣薇电子
// 修改内容   : 创建文件
//版权所有，盗版必究。
//Copyright(C) 欣薇电子2024/11/25
//All rights reserved
//******************************************************************************/

#include "stm32f10x.h"                  // Device header
#include "delay.h"
#include "sys.h"  
#include "beep.h" 

int main(void)
 {    

    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);     

    BEEP_Init(); 

    while(1)
    {                
       play_music();        
    }    
}
