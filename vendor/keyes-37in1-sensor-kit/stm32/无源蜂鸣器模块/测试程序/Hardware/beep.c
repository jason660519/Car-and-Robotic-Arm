#include "beep.h"
#include "delay.h"

 int melody[] = {50, 50, 50, 50, 200, 200, 200, 400, 400, 500, 500, 500};
 
void BEEP_Init(void)
{ 
 GPIO_InitTypeDef  GPIO_InitStructure; 
 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);   
 GPIO_InitStructure.GPIO_Pin = GPIO_Pin_11;  
 GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP; 
 GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
 GPIO_Init(GPIOA, &GPIO_InitStructure);
 GPIO_ResetBits(GPIOA,GPIO_Pin_11);
    
// GPIO_SetBits(GPIOA,GPIO_Pin_11);
}

void Sound(u16 frq)
{
    u32 time;
    if(frq != 1000)
    {
        time = 500000/((u32)frq);
        BEEP = 1;
        Delay_us(time);
        BEEP = 0;
        Delay_us(time);
    }else
        Delay_us(1000);
}
void Sound2(u16 time)
{
    BEEP = 1;
    Delay_ms(time);
    BEEP = 0;
    Delay_ms(time);
}

void play_successful(void)
{
    int id=0;
    for(id = 0 ;id < 12 ;id++)
    {
        Sound2(melody[id]);
    }
}
void play_failed(void)
{
    int id=0;
    for(id = 11 ;id >=0 ;id--)
    {
        Sound2(melody[id]);
    }
}
void play_music(void)
{    

    
//生日快乐歌
                  // 0   1   2   3   4   5   6   7  低1  低2 低3 低4 低5 低6低7
    uc16 tone[] ={250,262,294,330,350,393,441,495,525,589,661,700,786,882,990}; //音调        
    u8 music[]={5,5,6,5,8,7,5,5,6,5,9,8,5,5,12,10,8,7,6,11,
                  11,10,8,9,8,5,5,8,5,5,12,10,8,7,6,11,11,10,8,9,8    //乐谱音调
    };     
        u8 time[] = {1,2,2,2,2,4,1,2,2,2,2,4,1,2,2,2,1,4,
                      4,1,2,2,2,2,4,1,2,4,1,2,2,2,1,4, 4,1,2,2,2,2,4,4        //节拍时间
        }; 
                    
    u32 yanshi;
    u16 i,e;
    yanshi = 10;
    for(i=0;i<sizeof(music)/sizeof(music[0]);i++){
        for(e=0;e<((u16)time[i])*tone[music[i]]/yanshi;e++){
            Sound((u32)tone[music[i]]);
        }    
    }
}
