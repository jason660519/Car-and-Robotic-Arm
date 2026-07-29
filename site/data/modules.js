/**
 * 零件庫存資料 —— 中英文共用的單一真實來源。
 *
 * 不要在 HTML 裡再放一份。頁面用法：
 *
 *   <script src="../data/modules.js"></script>
 *   const MODULES_DATA = buildModules('zh', '../../');
 *
 * images 存的是相對 repo 根目錄的路徑，第二個參數是頁面到根目錄的前綴。
 * 新增模組請照 CONVENTIONS.md §3.3 先配流水號再補進這裡。
 */
const MODULES = [
  {
    "id": "mod-01",
    "number": "01/27/86/87",
    "name": "Waveshare Pan-Tilt HAT (Rev 2.1)",
    "category": "motion",
    "tags": [
      "RaspberryPi",
      "PCA9685",
      "TSL2591",
      "I2C",
      "Servo"
    ],
    "images": [
      "assets/inventory/001_Waveshare_PanTilt_HAT_Back.jpg",
      "assets/inventory/027_Waveshare_PanTilt_HAT_Front.jpg",
      "assets/inventory/086_Waveshare_PanTilt_HAT_Rev21_Front.jpg",
      "assets/inventory/087_Waveshare_PanTilt_HAT_Rev21_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "Waveshare 雙軸雲台伺服馬達驅動擴充板",
        "desc": "專為樹莓派設計的 2-DOF 雙軸雲台擴充板，板載 PCA9685 PWM 驅動晶片與 TSL2591 光強感測器，可同時控制 2 組雲台舵機並感測環境光照強度。",
        "specs": [
          {
            "label": "驅動晶片",
            "val": "PCA9685 (PWM) + TSL2591 (Ambient Light)"
          },
          {
            "label": "通訊介面",
            "val": "I2C (PCA9685預設位址 0x40, TSL2591位址 0x29)"
          },
          {
            "label": "工作電壓",
            "val": "5V (接線柱支援外部舵機獨立供電)"
          },
          {
            "label": "適用旋轉角度",
            "val": "水平 180° / 垂直 180° 雲台結構"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 5V"
          },
          {
            "pin": "GND",
            "conn": "Arduino GND"
          },
          {
            "pin": "SDA",
            "conn": "Arduino A4 (或 SDA)"
          },
          {
            "pin": "SCL",
            "conn": "Arduino A5 (或 SCL)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "VCC",
            "conn": "STM32 3.3V / 5V"
          },
          {
            "pin": "GND",
            "conn": "STM32 GND"
          },
          {
            "pin": "SDA",
            "conn": "STM32 PB7 (I2C1_SDA)"
          },
          {
            "pin": "SCL",
            "conn": "STM32 PB6 (I2C1_SCL)"
          }
        ],
        "codeSnippet": "// Arduino PCA9685 雲台舵機控制範例\n#include <Wire.h>\n#include <Adafruit_PWMServoDriver.h>\n\nAdafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);\n\nvoid setup() {\n  pwm.begin();\n  pwm.setPWMFreq(50); // 舵機頻率 50Hz\n}\n\nvoid loop() {\n  // 水平軸 (Channel 0) 轉至中位 90 度 (約 307 pulse)\n  pwm.setPWM(0, 0, 307);\n  // 垂直軸 (Channel 1) 轉至中位 90 度\n  pwm.setPWM(1, 0, 307);\n  delay(1000);\n}"
      },
      "en": {
        "title": "Waveshare Pan-Tilt HAT (Rev 2.1)",
        "desc": "A 2-DOF Pan-Tilt expansion HAT designed for Raspberry Pi. Features onboard PCA9685 PWM driver chip and TSL2591 ambient light sensor, capable of controlling 2 servos while measuring light intensity.",
        "specs": [
          {
            "label": "Driver IC",
            "val": "PCA9685 (PWM) + TSL2591 (Ambient Light)"
          },
          {
            "label": "Interface",
            "val": "I2C (PCA9685 Address 0x40, TSL2591 Address 0x29)"
          },
          {
            "label": "Voltage",
            "val": "5V (Screw terminal supports independent external servo power)"
          },
          {
            "label": "Rotation Angle",
            "val": "Pan 180° / Tilt 180° mechanical structure"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 5V"
          },
          {
            "pin": "GND",
            "conn": "Arduino GND"
          },
          {
            "pin": "SDA",
            "conn": "Arduino A4 (or SDA)"
          },
          {
            "pin": "SCL",
            "conn": "Arduino A5 (or SCL)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "VCC",
            "conn": "STM32 3.3V / 5V"
          },
          {
            "pin": "GND",
            "conn": "STM32 GND"
          },
          {
            "pin": "SDA",
            "conn": "STM32 PB7 (I2C1_SDA)"
          },
          {
            "pin": "SCL",
            "conn": "STM32 PB6 (I2C1_SCL)"
          }
        ],
        "codeSnippet": "// Arduino PCA9685 Pan-Tilt Servo Example\n#include <Wire.h>\n#include <Adafruit_PWMServoDriver.h>\n\nAdafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);\n\nvoid setup() {\n  pwm.begin();\n  pwm.setPWMFreq(50); // Servo frequency 50Hz\n}\n\nvoid loop() {\n  // Pan axis (Channel 0) to neutral 90 deg (~307 pulse)\n  pwm.setPWM(0, 0, 307);\n  // Tilt axis (Channel 1) to neutral 90 deg\n  pwm.setPWM(1, 0, 307);\n  delay(1000);\n}"
      }
    }
  },
  {
    "id": "mod-26",
    "number": "26/88",
    "name": "Arduino UNO R3 Controller Board",
    "category": "controllers",
    "tags": [
      "Arduino",
      "ATmega328P",
      "CH340",
      "MCU"
    ],
    "images": [
      "assets/inventory/026_Arduino_UNO_R3_Board.jpg",
      "assets/inventory/088_Arduino_UNO_R3_Blue_Board.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "Arduino UNO R3 微控制器核心開發板",
        "desc": "最具代表性的開源微控制器核心板，採用 ATmega328P 主晶片，具備 14 組數位 GPIO（含 6 組 PWM）與 6 組類比輸入，適合機器人控制與感測器實驗。",
        "specs": [
          {
            "label": "微控制器",
            "val": "ATmega328P (8-bit AVR 16MHz)"
          },
          {
            "label": "工作電壓",
            "val": "5V (VIN 支援 7-12V 輸入)"
          },
          {
            "label": "IO 數量",
            "val": "14 Digital (6 PWM), 6 Analog (A0-A5)"
          },
          {
            "label": "通訊協定",
            "val": "UART, SPI, I2C"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "USB",
            "conn": "電腦程式燒錄與 Serial 監控"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "TXD / RXD",
            "conn": "可經由 UART 與 STM32 雙機通訊"
          }
        ],
        "codeSnippet": "void setup() {\n  pinMode(LED_BUILTIN, OUTPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  digitalWrite(LED_BUILTIN, HIGH);\n  delay(500);\n  digitalWrite(LED_BUILTIN, LOW);\n  delay(500);\n}"
      },
      "en": {
        "title": "Arduino UNO R3 Controller Board",
        "desc": "Standard open-source microcontroller board powered by the ATmega328P chip. Features 14 digital I/O pins (6 PWM outputs), 6 analog inputs, and onboard USB programming.",
        "specs": [
          {
            "label": "Microcontroller",
            "val": "ATmega328P (8-bit AVR 16MHz)"
          },
          {
            "label": "Operating Voltage",
            "val": "5V (VIN supports 7-12V input)"
          },
          {
            "label": "I/O Count",
            "val": "14 Digital (6 PWM), 6 Analog (A0-A5)"
          },
          {
            "label": "Protocols",
            "val": "UART, SPI, I2C"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "USB",
            "conn": "PC Program Flashing & Serial Monitor"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "TXD / RXD",
            "conn": "Connect via UART for Master-Slave communication"
          }
        ],
        "codeSnippet": "void setup() {\n  pinMode(LED_BUILTIN, OUTPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  digitalWrite(LED_BUILTIN, HIGH);\n  delay(500);\n  digitalWrite(LED_BUILTIN, LOW);\n  delay(500);\n}"
      }
    }
  },
  {
    "id": "mod-54",
    "number": "54/55/65/66/67",
    "name": "STM32F103C8T6 ARM Cortex-M3 (Blue Pill)",
    "category": "controllers",
    "tags": [
      "STM32",
      "ARM",
      "Cortex-M3",
      "72MHz"
    ],
    "images": [
      "assets/inventory/054_STM32F103C8T6_BluePill_Board1_Front.jpg",
      "assets/inventory/055_STM32F103C8T6_BluePill_Board1_Back.jpg",
      "assets/inventory/065_STM32F103C8T6_BluePill_Board2_Front.jpg",
      "assets/inventory/066_STM32F103C8T6_BluePill_Board2_Back.jpg",
      "assets/inventory/067_STM32F103C8T6_BluePill_Board3_Front.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "STM32F103C8T6 藍藥丸開發板",
        "desc": "經典 STM32 ARM Cortex-M3 高效能微控制器開發板（俗稱 Blue Pill），擁有 72MHz 核心頻率、64KB Flash、20KB SRAM 與豐富的外設資源。",
        "specs": [
          {
            "label": "處理器核心",
            "val": "ARM Cortex-M3 (72MHz)"
          },
          {
            "label": "記憶體容量",
            "val": "64 KB Flash, 20 KB SRAM"
          },
          {
            "label": "通訊介面",
            "val": "3x USART, 2x SPI, 2x I2C, 1x CAN, USB 2.0"
          },
          {
            "label": "燒錄介面",
            "val": "SWD (SWDIO/SWCLK) 或 Serial Bootloader"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "STM32Duino",
            "conn": "支援 Arduino IDE STM32 板卡擴充"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "PA9 (TX)",
            "conn": "USB轉TTL RX"
          },
          {
            "pin": "PA10 (RX)",
            "conn": "USB轉TTL TX"
          },
          {
            "pin": "3.3V / GND",
            "conn": "供電端子"
          }
        ],
        "codeSnippet": "// STM32 HAL GPIO 閃爍燈範例\n#include \"stm32f1xx_hal.h\"\nint main(void) {\n  HAL_Init();\n  __HAL_RCC_GPIOC_CLK_ENABLE();\n  GPIO_InitTypeDef GPIO_InitStruct = {0};\n  GPIO_InitStruct.Pin = GPIO_PIN_13;\n  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;\n  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;\n  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);\n  while (1) {\n    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);\n    HAL_Delay(500);\n  }\n}"
      },
      "en": {
        "title": "STM32F103C8T6 ARM Cortex-M3 (Blue Pill)",
        "desc": "High-performance ARM Cortex-M3 microcontroller development board ('Blue Pill'). Features 72MHz clock rate, 64KB Flash, 20KB SRAM, and rich hardware peripherals.",
        "specs": [
          {
            "label": "Core",
            "val": "ARM Cortex-M3 (72MHz)"
          },
          {
            "label": "Memory",
            "val": "64 KB Flash, 20 KB SRAM"
          },
          {
            "label": "Peripherals",
            "val": "3x USART, 2x SPI, 2x I2C, 1x CAN, USB 2.0"
          },
          {
            "label": "Debugging",
            "val": "SWD Header (SWDIO/SWCLK)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "STM32Duino",
            "conn": "Supports Arduino IDE via STM32 Core extension"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "PA9 (TX)",
            "conn": "USB-to-TTL RX"
          },
          {
            "pin": "PA10 (RX)",
            "conn": "USB-to-TTL TX"
          },
          {
            "pin": "3.3V / GND",
            "conn": "Power Pins"
          }
        ],
        "codeSnippet": "// STM32 HAL GPIO Blink Example\n#include \"stm32f1xx_hal.h\"\nint main(void) {\n  HAL_Init();\n  __HAL_RCC_GPIOC_CLK_ENABLE();\n  GPIO_InitTypeDef GPIO_InitStruct = {0};\n  GPIO_InitStruct.Pin = GPIO_PIN_13;\n  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;\n  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;\n  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);\n  while (1) {\n    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);\n    HAL_Delay(500);\n  }\n}"
      }
    }
  },
  {
    "id": "mod-56",
    "number": "56/57",
    "name": "GY-521 MPU6050 6-DOF IMU Sensor",
    "category": "sensors",
    "tags": [
      "Sensor",
      "MPU6050",
      "I2C",
      "Gyro",
      "Accel"
    ],
    "images": [
      "assets/inventory/056_GY521_MPU6050_Sensor_Front.jpg",
      "assets/inventory/057_GY521_MPU6050_Sensor_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "GY-521 MPU6050 六軸姿態與加速度感測器",
        "desc": "整合 3 軸陀螺儀與 3 軸加速度計的 6 自由度姿態感測器模組，內建 DMP (Digital Motion Processor) 硬體姿勢解算晶片，廣泛用於平衡小車與四軸飛行器。",
        "specs": [
          {
            "label": "晶片型號",
            "val": "MPU-6050"
          },
          {
            "label": "通訊介面",
            "val": "I2C (位址 0x68，AD0 拉高為 0x69)"
          },
          {
            "label": "工作電壓",
            "val": "3.3V - 5V (板載 LDO 穩壓)"
          },
          {
            "label": "量程範圍",
            "val": "加速度 ±2g/±4g/±8g/±16g, 角速度 ±250/500/1000/2000 °/s"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 5V / 3.3V"
          },
          {
            "pin": "GND",
            "conn": "Arduino GND"
          },
          {
            "pin": "SCL",
            "conn": "Arduino A5"
          },
          {
            "pin": "SDA",
            "conn": "Arduino A4"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "VCC",
            "conn": "STM32 3.3V"
          },
          {
            "pin": "GND",
            "conn": "STM32 GND"
          },
          {
            "pin": "SCL",
            "conn": "STM32 PB6"
          },
          {
            "pin": "SDA",
            "conn": "STM32 PB7"
          }
        ],
        "codeSnippet": "// Arduino MPU6050 讀取範例\n#include <Wire.h>\nconst int MPU = 0x68;\nint16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;\nvoid setup() {\n  Wire.begin();\n  Wire.beginTransmission(MPU);\n  Wire.write(0x6B); // 喚醒 MPU6050\n  Wire.write(0);\n  Wire.endTransmission(true);\n  Serial.begin(9600);\n}\nvoid loop() {\n  Wire.beginTransmission(MPU);\n  Wire.write(0x3B);\n  Wire.endTransmission(false);\n  Wire.requestFrom(MPU, 14, true);\n  AcX = Wire.read()<<8|Wire.read();\n  AcY = Wire.read()<<8|Wire.read();\n  AcZ = Wire.read()<<8|Wire.read();\n  Serial.print(\"AcX = \"); Serial.println(AcX);\n  delay(333);\n}"
      },
      "en": {
        "title": "GY-521 MPU6050 6-DOF IMU Sensor",
        "desc": "6-DOF Motion Tracking module combining a 3-axis gyroscope and a 3-axis accelerometer with an onboard Digital Motion Processor (DMP). Ideal for self-balancing robots and quadcopters.",
        "specs": [
          {
            "label": "Chipset",
            "val": "MPU-6050"
          },
          {
            "label": "Protocol",
            "val": "I2C (Address 0x68 default, 0x69 when AD0 High)"
          },
          {
            "label": "Voltage",
            "val": "3.3V - 5V (Onboard LDO regulator)"
          },
          {
            "label": "Range",
            "val": "Accel ±2g/±4g/±8g/±16g, Gyro ±250/500/1000/2000 °/s"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 5V / 3.3V"
          },
          {
            "pin": "GND",
            "conn": "Arduino GND"
          },
          {
            "pin": "SCL",
            "conn": "Arduino A5"
          },
          {
            "pin": "SDA",
            "conn": "Arduino A4"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "VCC",
            "conn": "STM32 3.3V"
          },
          {
            "pin": "GND",
            "conn": "STM32 GND"
          },
          {
            "pin": "SCL",
            "conn": "STM32 PB6"
          },
          {
            "pin": "SDA",
            "conn": "STM32 PB7"
          }
        ],
        "codeSnippet": "// Arduino MPU6050 Data Read\n#include <Wire.h>\nconst int MPU = 0x68;\nint16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;\nvoid setup() {\n  Wire.begin();\n  Wire.beginTransmission(MPU);\n  Wire.write(0x6B); // Wake up MPU6050\n  Wire.write(0);\n  Wire.endTransmission(true);\n  Serial.begin(9600);\n}\nvoid loop() {\n  Wire.beginTransmission(MPU);\n  Wire.write(0x3B);\n  Wire.endTransmission(false);\n  Wire.requestFrom(MPU, 14, true);\n  AcX = Wire.read()<<8|Wire.read();\n  AcY = Wire.read()<<8|Wire.read();\n  AcZ = Wire.read()<<8|Wire.read();\n  Serial.print(\"AcX = \"); Serial.println(AcX);\n  delay(333);\n}"
      }
    }
  },
  {
    "id": "mod-41",
    "number": "41/42",
    "name": "Yahboom 4-Channel IR Tracing Sensor",
    "category": "sensors",
    "tags": [
      "Sensor",
      "Infrared",
      "Tracing",
      "LineFollower"
    ],
    "images": [
      "assets/inventory/041_Yahboom_4Channel_Tracing_Sensor_Back.jpg",
      "assets/inventory/042_Yahboom_4Channel_Tracing_Sensor_Front.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "Yahboom 四路紅外線循跡感測器模組",
        "desc": "專為智慧循跡小車設計的四路高靈敏度紅外線反射式感測器，採用 LM339 比較器，可精確分辨黑線與白底，提供高/低電位數位訊號輸出。",
        "specs": [
          {
            "label": "通道數量",
            "val": "4 通道獨立輸出 (Out1 - Out4)"
          },
          {
            "label": "感測距離",
            "val": "1cm - 3cm (可透過電位器調整靈敏度)"
          },
          {
            "label": "輸出訊號",
            "val": "數位 TTL 電位 (偵測到黑線輸出高電位/低電位)"
          },
          {
            "label": "工作電壓",
            "val": "3.3V - 5V"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 5V"
          },
          {
            "pin": "GND",
            "conn": "Arduino GND"
          },
          {
            "pin": "Out1 - Out4",
            "conn": "Arduino D2, D3, D4, D5"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "VCC",
            "conn": "STM32 3.3V"
          },
          {
            "pin": "GND",
            "conn": "STM32 GND"
          },
          {
            "pin": "Out1 - Out4",
            "conn": "STM32 PA0, PA1, PA2, PA3"
          }
        ],
        "codeSnippet": "void setup() {\n  for(int i=2; i<=5; i++) pinMode(i, INPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  int s1 = digitalRead(2);\n  int s2 = digitalRead(3);\n  int s3 = digitalRead(4);\n  int s4 = digitalRead(5);\n  Serial.print(\"Tracing: \");\n  Serial.print(s1); Serial.print(s2);\n  Serial.print(s3); Serial.println(s4);\n  delay(100);\n}"
      },
      "en": {
        "title": "Yahboom 4-Channel IR Tracing Sensor",
        "desc": "High-sensitivity 4-channel infrared line follower module using LM339 comparator. Distinguishes black line on white surface and provides TTL digital outputs.",
        "specs": [
          {
            "label": "Channels",
            "val": "4 Channels (Out1 - Out4)"
          },
          {
            "label": "Detection Distance",
            "val": "1cm - 3cm (Adjustable via potentiometers)"
          },
          {
            "label": "Signal Type",
            "val": "Digital TTL (High/Low output when line detected)"
          },
          {
            "label": "Voltage",
            "val": "3.3V - 5V"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 5V"
          },
          {
            "pin": "GND",
            "conn": "Arduino GND"
          },
          {
            "pin": "Out1 - Out4",
            "conn": "Arduino D2, D3, D4, D5"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "VCC",
            "conn": "STM32 3.3V"
          },
          {
            "pin": "GND",
            "conn": "STM32 GND"
          },
          {
            "pin": "Out1 - Out4",
            "conn": "STM32 PA0, PA1, PA2, PA3"
          }
        ],
        "codeSnippet": "void setup() {\n  for(int i=2; i<=5; i++) pinMode(i, INPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  int s1 = digitalRead(2);\n  int s2 = digitalRead(3);\n  int s3 = digitalRead(4);\n  int s4 = digitalRead(5);\n  Serial.print(\"Line Status: \");\n  Serial.print(s1); Serial.print(s2);\n  Serial.print(s3); Serial.println(s4);\n  delay(100);\n}"
      }
    }
  },
  {
    "id": "mod-43",
    "number": "43/44",
    "name": "WS2812B 8x8 RGB LED Matrix Panel",
    "category": "display_audio",
    "tags": [
      "Display",
      "WS2812B",
      "RGB",
      "NeoPixel"
    ],
    "images": [
      "assets/inventory/043_WS2812B_8x8_RGB_LED_Matrix_Front.jpg",
      "assets/inventory/044_WS2812B_8x8_RGB_LED_Matrix_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "WS2812B 8x8 矩陣屏 (64像素全彩 RGB LED)",
        "desc": "包含 64 顆（8x8）可單獨定址全彩 RGB LED 的矩陣陣列，採用單線歸零碼通訊協定，僅需 1 根 GPIO 即可控制 1670 萬種色彩與動畫圖案。",
        "specs": [
          {
            "label": "LED 型號",
            "val": "WS2812B 5050 RGB"
          },
          {
            "label": "像素點數",
            "val": "64 點 (8 欄 x 8 列)"
          },
          {
            "label": "通訊介面",
            "val": "Single-line NZR Protocol (DIN / DOUT 串接)"
          },
          {
            "label": "工作電壓",
            "val": "5V DC (全亮最大電流約 3.8A，建議外接電源)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "5V 獨立電源 (與 Arduino 共地)"
          },
          {
            "pin": "GND",
            "conn": "GND"
          },
          {
            "pin": "DIN",
            "conn": "Arduino D6 (串聯 470Ω 電阻)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "DIN",
            "conn": "STM32 PB15 (SPI DMA 或 PWM+DMA)"
          }
        ],
        "codeSnippet": "// Arduino FastLED WS2812B 範例\n#include <FastLED.h>\n#define NUM_LEDS 64\n#define DATA_PIN 6\nCRGB leds[NUM_LEDS];\n\nvoid setup() {\n  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);\n}\nvoid loop() {\n  for(int i = 0; i < NUM_LEDS; i++) {\n    leds[i] = CRGB::Red;\n    FastLED.show();\n    delay(20);\n    leds[i] = CRGB::Black;\n  }\n}"
      },
      "en": {
        "title": "WS2812B 8x8 RGB LED Matrix Panel",
        "desc": "64 (8x8) individually addressable RGB LEDs on a compact matrix panel. Single-wire NZR protocol control over 16.7M colors per pixel.",
        "specs": [
          {
            "label": "LED Type",
            "val": "WS2812B 5050 RGB"
          },
          {
            "label": "Pixel Count",
            "val": "64 Pixels (8 Rows x 8 Columns)"
          },
          {
            "label": "Protocol",
            "val": "Single-line NZR Protocol (DIN / DOUT daisy-chain)"
          },
          {
            "label": "Power",
            "val": "5V DC (~3.8A max full white, external supply recommended)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "External 5V Power (Common GND)"
          },
          {
            "pin": "GND",
            "conn": "GND"
          },
          {
            "pin": "DIN",
            "conn": "Arduino D6 (in series with 470Ω resistor)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "DIN",
            "conn": "STM32 PB15 (SPI DMA or PWM+DMA)"
          }
        ],
        "codeSnippet": "// Arduino FastLED WS2812B Example\n#include <FastLED.h>\n#define NUM_LEDS 64\n#define DATA_PIN 6\nCRGB leds[NUM_LEDS];\n\nvoid setup() {\n  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);\n}\nvoid loop() {\n  for(int i = 0; i < NUM_LEDS; i++) {\n    leds[i] = CRGB::Red;\n    FastLED.show();\n    delay(20);\n    leds[i] = CRGB::Black;\n  }\n}"
      }
    }
  },
  {
    "id": "mod-72",
    "number": "72/73",
    "name": "ESP32 GRBL CNC & Laser Control Board",
    "category": "motion",
    "tags": [
      "Motion",
      "ESP32",
      "GRBL",
      "CNC",
      "Stepper"
    ],
    "images": [
      "assets/inventory/072_ESP32_GRBL_CNC_Control_Board_Front.jpg",
      "assets/inventory/073_ESP32_GRBL_CNC_Control_Board_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "ESP32 三軸 GRBL CNC/雷射控制主板",
        "desc": "基於 ESP32 雙核處理器的 CNC/雷射雕刻機控制主板，支援 GRBL 韌體、Wi-Fi/藍牙無線控制，可插入 3 組 A4988/DRV8825 步進馬達驅動模組。",
        "specs": [
          {
            "label": "主控晶片",
            "val": "ESP32-WROOM-32D (240MHz 雙核)"
          },
          {
            "label": "軸數支援",
            "val": "X, Y, Z 三軸獨立步進馬達驅動槽"
          },
          {
            "label": "擴充介面",
            "val": "主軸 PWM / 雷射頭控制, 極限開關, 離線手持控制器端子"
          },
          {
            "label": "輸入電壓",
            "val": "DC 12V - 24V"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Micro-USB",
            "conn": "直接使用 Web界面或 Universal Gcode Sender 燒錄控板"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "UART",
            "conn": "可經由 TX/RX 傳送 G-code 命令"
          }
        ],
        "codeSnippet": "// GRBL 常用 G-Code 指令範例\n$X          // 解除鎖定\nG21 G90     // 公制單位, 絕對座標\nG0 X10 Y20  // 快速移動至 (10, 20)\nM3 S500     // 啟動雷射 / 主軸 PWM 功率 50%"
      },
      "en": {
        "title": "ESP32 GRBL CNC & Laser Control Board",
        "desc": "Dual-core ESP32 motion controller board for 3-axis CNC routers and laser engravers. Supports GRBL firmware, Wi-Fi/Bluetooth web interface, and 3x A4988/DRV8825 stepper sockets.",
        "specs": [
          {
            "label": "Main MCU",
            "val": "ESP32-WROOM-32D (240MHz Dual-Core)"
          },
          {
            "label": "Axes",
            "val": "X, Y, Z independent stepper driver sockets"
          },
          {
            "label": "Peripherals",
            "val": "Spindle PWM / Laser output, Limit switch headers, Handheld controller port"
          },
          {
            "label": "Voltage",
            "val": "DC 12V - 24V"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Micro-USB",
            "conn": "Flash GRBL firmware or upload via WebUI / UGS"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "UART",
            "conn": "Send G-Code commands via TX/RX"
          }
        ],
        "codeSnippet": "// Common GRBL G-Code Commands\n$X          // Unlock alarm\nG21 G90     // Metric units, absolute positioning\nG0 X10 Y20  // Rapid motion to (10, 20)\nM3 S500     // Turn on Spindle/Laser PWM 50%"
      }
    }
  },
  {
    "id": "mod-74",
    "number": "74/75",
    "name": "STM32F4 GRBL-HAL 6-Axis Motion Control Board",
    "category": "motion",
    "tags": [
      "STM32",
      "GRBL-HAL",
      "6Axis",
      "Motion",
      "CNC"
    ],
    "images": [
      "assets/inventory/074_STM32F4_GRBL_HAL_6Axis_Control_Board_Front.jpg",
      "assets/inventory/075_STM32F4_GRBL_HAL_6Axis_Control_Board_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "STM32F4 GRBL-HAL 六軸運動控制器主板",
        "desc": "高階 6 軸 GRBL-HAL 運動控制主板，採用 STM32F407 高效能 Cortex-M4F 晶片，支援高脈衝頻率、網路卡介面、SD 卡離線列印與多軸聯動。",
        "specs": [
          {
            "label": "處理器",
            "val": "STM32F407 (168MHz Cortex-M4F + FPU)"
          },
          {
            "label": "控制軸數",
            "val": "6 軸 (X, Y, Z, A, B, C) 脈衝/方向訊號輸出"
          },
          {
            "label": "週邊介面",
            "val": "Ethernet RJ45, MicroSD 卡槽, USB, 工業級光耦隔離"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "GRBL-HAL",
            "conn": "透過 WebUI 或 乙太網路發送 GCode 串流"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Step/Dir",
            "conn": "硬體級 Timers 產生最高 300kHz 步進脈衝"
          }
        ],
        "codeSnippet": "// grblHAL 韌體配置\n#define N_AXIS 6\n#define SPINDLE_PWM_FREQ 5000\n#define STEP_PULSE_LATENCY 2"
      },
      "en": {
        "title": "STM32F4 GRBL-HAL 6-Axis Motion Control Board",
        "desc": "Industrial-grade 6-axis motion controller board running grblHAL firmware on an STM32F407 168MHz MCU. Supports high pulse rates, Ethernet streaming, and SD card offline operation.",
        "specs": [
          {
            "label": "MCU",
            "val": "STM32F407 (168MHz Cortex-M4F + FPU)"
          },
          {
            "label": "Axes",
            "val": "6 Axes (X, Y, Z, A, B, C) Step/Dir outputs"
          },
          {
            "label": "Interfaces",
            "val": "Ethernet RJ45, MicroSD Card, USB, Optocoupler isolation"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "GRBL-HAL",
            "conn": "Stream G-Code via WebUI or Ethernet"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Step/Dir",
            "conn": "Hardware Timers generate up to 300kHz step frequency"
          }
        ],
        "codeSnippet": "// grblHAL Firmware Config\n#define N_AXIS 6\n#define SPINDLE_PWM_FREQ 5000\n#define STEP_PULSE_LATENCY 2"
      }
    }
  },
  {
    "id": "mod-76",
    "number": "76/77",
    "name": "Waveshare Barcode Scanner Module",
    "category": "sensors",
    "tags": [
      "Sensor",
      "Camera",
      "Barcode",
      "QRCode",
      "UART"
    ],
    "images": [
      "assets/inventory/076_Waveshare_Barcode_Scanner_Module_Front.jpg",
      "assets/inventory/077_Waveshare_Barcode_Scanner_Module_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "Waveshare 條碼 / 二維碼光學掃描解碼模組",
        "desc": "高感度光學影像掃描模組，可精確讀取紙質與螢幕上的一維條碼 (1D) 與二維碼 (2D QR Code)，支援 USB 與 UART 序列埠直接自動輸出解碼文字。",
        "specs": [
          {
            "label": "辨識類型",
            "val": "QR Code, Data Matrix, PDF417, Code 128, EAN 等"
          },
          {
            "label": "通訊介面",
            "val": "UART (波特率 9600 預設) / USB HID / USB 虛擬 Serial"
          },
          {
            "label": "光源",
            "val": "板載白色 LED 補光燈 + 綠色瞄準光束"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "5V"
          },
          {
            "pin": "GND",
            "conn": "GND"
          },
          {
            "pin": "TX",
            "conn": "Arduino D2 (SoftwareSerial RX)"
          },
          {
            "pin": "RX",
            "conn": "Arduino D3 (SoftwareSerial TX)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "TX",
            "conn": "STM32 PA10 (USART1_RX)"
          },
          {
            "pin": "RX",
            "conn": "STM32 PA9 (USART1_TX)"
          }
        ],
        "codeSnippet": "// Arduino 讀取 Barcode 解碼資料範例\n#include <SoftwareSerial.h>\nSoftwareSerial scanner(2, 3); // RX, TX\n\nvoid setup() {\n  Serial.begin(9600);\n  scanner.begin(9600);\n}\nvoid loop() {\n  if (scanner.available()) {\n    char c = scanner.read();\n    Serial.print(c);\n  }\n}"
      },
      "en": {
        "title": "Waveshare Barcode Scanner Module",
        "desc": "High-sensitivity optical barcode & QR code decoding camera module. Reads 1D/2D codes from paper or digital screens and outputs decoded strings via UART / USB.",
        "specs": [
          {
            "label": "Supported Decodes",
            "val": "QR Code, Data Matrix, PDF417, Code 128, EAN, etc."
          },
          {
            "label": "Communication",
            "val": "UART (9600 baud default) / USB HID / USB Virtual COM"
          },
          {
            "label": "Illumination",
            "val": "Onboard white LED fill-light + green targeting LED"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "5V"
          },
          {
            "pin": "GND",
            "conn": "GND"
          },
          {
            "pin": "TX",
            "conn": "Arduino D2 (SoftwareSerial RX)"
          },
          {
            "pin": "RX",
            "conn": "Arduino D3 (SoftwareSerial TX)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "TX",
            "conn": "STM32 PA10 (USART1_RX)"
          },
          {
            "pin": "RX",
            "conn": "STM32 PA9 (USART1_TX)"
          }
        ],
        "codeSnippet": "// Arduino Barcode Reader Code\n#include <SoftwareSerial.h>\nSoftwareSerial scanner(2, 3); // RX, TX\n\nvoid setup() {\n  Serial.begin(9600);\n  scanner.begin(9600);\n}\nvoid loop() {\n  if (scanner.available()) {\n    char c = scanner.read();\n    Serial.print(c);\n  }\n}"
      }
    }
  },
  {
    "id": "mod-78",
    "number": "78/79",
    "name": "Waveshare ToF Laser Distance Sensor",
    "category": "sensors",
    "tags": [
      "Sensor",
      "Laser",
      "ToF",
      "Distance",
      "UART"
    ],
    "images": [
      "assets/inventory/078_Waveshare_Laser_Sensor_Front.jpg",
      "assets/inventory/079_Waveshare_Laser_Sensor_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "Waveshare 雷射飛行時間 (ToF) 測距感測器",
        "desc": "基於 ToF (Time-of-Flight) 光學飛行時間原理的雷射距離感測器，量測範圍廣、精度高，不受目標物顏色與反射率影響。",
        "specs": [
          {
            "label": "測量範圍",
            "val": "4cm - 400cm (4公尺)"
          },
          {
            "label": "通訊介面",
            "val": "UART 序列埠 (波特率 115200) / I2C"
          },
          {
            "label": "精度與解析度",
            "val": "毫米級解析度 (±1cm)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "5V"
          },
          {
            "pin": "GND",
            "conn": "GND"
          },
          {
            "pin": "TX",
            "conn": "Arduino D2 (SoftwareSerial RX)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "TX",
            "conn": "STM32 PA3 (USART2_RX)"
          }
        ],
        "codeSnippet": "// ToF 雷射資料封包解析\nvoid parseToFData(uint8_t buf[]) {\n  if(buf[0] == 0x57 && buf[1] == 0x00) {\n    uint32_t distance_mm = buf[4] | (buf[5] << 8) | (buf[6] << 16);\n    Serial.print(\"Distance: \"); Serial.print(distance_mm); Serial.println(\" mm\");\n  }\n}"
      },
      "en": {
        "title": "Waveshare ToF Laser Distance Sensor",
        "desc": "Time-of-Flight (ToF) optical distance measurement sensor. High accuracy and wide range, unaffected by target surface color or reflectivity.",
        "specs": [
          {
            "label": "Range",
            "val": "4cm - 400cm (4 meters)"
          },
          {
            "label": "Interface",
            "val": "UART Serial (115200 baud) / I2C"
          },
          {
            "label": "Precision",
            "val": "Millimeter-level resolution (±1cm)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "5V"
          },
          {
            "pin": "GND",
            "conn": "GND"
          },
          {
            "pin": "TX",
            "conn": "Arduino D2 (SoftwareSerial RX)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "TX",
            "conn": "STM32 PA3 (USART2_RX)"
          }
        ],
        "codeSnippet": "// ToF Packet Parser\nvoid parseToFData(uint8_t buf[]) {\n  if(buf[0] == 0x57 && buf[1] == 0x00) {\n    uint32_t distance_mm = buf[4] | (buf[5] << 8) | (buf[6] << 16);\n    Serial.print(\"Distance: \"); Serial.print(distance_mm); Serial.println(\" mm\");\n  }\n}"
      }
    }
  },
  {
    "id": "mod-89",
    "number": "89",
    "name": "4-in-1 Mini Sensors Pack",
    "category": "sensors",
    "tags": [
      "Sensors",
      "Ultrasonic",
      "Power",
      "WaterSensor",
      "Buck"
    ],
    "images": [
      "assets/inventory/089_Four_Mini_Modules_Buck_Power_Ultrasonic_Water.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "4項經典迷你模組組裝套裝",
        "desc": "包含 4 個必備小巧實用的機器人開發模組：MP1584EN 可調降壓模組、HW-131 麵包板電源、HC-SR04 超音波距離感測器與水位/雨滴感測器。",
        "specs": [
          {
            "label": "1. 降壓模組",
            "val": "MP1584EN (輸入4.5V-28V, 輸出0.8V-20V 3A)"
          },
          {
            "label": "2. 超音波感測器",
            "val": "HC-SR04 (2cm-400cm 測距, Trig/Echo 觸發)"
          },
          {
            "label": "3. 水位感測器",
            "val": "Analog Depth Sensor (平行導線阻抗測量)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "HC-SR04 Trig",
            "conn": "Arduino D8"
          },
          {
            "pin": "HC-SR04 Echo",
            "conn": "Arduino D9"
          },
          {
            "pin": "Water Sensor S",
            "conn": "Arduino A0"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "HC-SR04 Trig",
            "conn": "STM32 PB5"
          },
          {
            "pin": "HC-SR04 Echo",
            "conn": "STM32 PB6"
          },
          {
            "pin": "Water Sensor S",
            "conn": "STM32 PA0 (ADC1_IN0)"
          }
        ],
        "codeSnippet": "// HC-SR04 超音波測距程式\nlong duration;\nint distance;\nvoid setup() {\n  pinMode(8, OUTPUT); // Trig\n  pinMode(9, INPUT);  // Echo\n  Serial.begin(9600);\n}\nvoid loop() {\n  digitalWrite(8, LOW); delayMicroseconds(2);\n  digitalWrite(8, HIGH); delayMicroseconds(10);\n  digitalWrite(8, LOW);\n  duration = pulseIn(9, HIGH);\n  distance = duration * 0.034 / 2;\n  Serial.print(\"Distance: \"); Serial.print(distance); Serial.println(\" cm\");\n  delay(200);\n}"
      },
      "en": {
        "title": "4-in-1 Mini Sensors Pack",
        "desc": "A compact 4-in-1 module kit containing MP1584EN step-down buck converter, HW-131 breadboard power supply, HC-SR04 ultrasonic distance sensor, and water depth sensor.",
        "specs": [
          {
            "label": "1. Buck Converter",
            "val": "MP1584EN (Input 4.5V-28V, Output 0.8V-20V 3A)"
          },
          {
            "label": "2. Ultrasonic Sensor",
            "val": "HC-SR04 (2cm-400cm distance, Trig/Echo pulse)"
          },
          {
            "label": "3. Water Depth Sensor",
            "val": "Analog Depth Sensor (Resistive impedance measurement)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "HC-SR04 Trig",
            "conn": "Arduino D8"
          },
          {
            "pin": "HC-SR04 Echo",
            "conn": "Arduino D9"
          },
          {
            "pin": "Water Sensor S",
            "conn": "Arduino A0"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "HC-SR04 Trig",
            "conn": "STM32 PB5"
          },
          {
            "pin": "HC-SR04 Echo",
            "conn": "STM32 PB6"
          },
          {
            "pin": "Water Sensor S",
            "conn": "STM32 PA0 (ADC1_IN0)"
          }
        ],
        "codeSnippet": "// HC-SR04 Ultrasonic Distance Measurement\nlong duration;\nint distance;\nvoid setup() {\n  pinMode(8, OUTPUT); // Trig\n  pinMode(9, INPUT);  // Echo\n  Serial.begin(9600);\n}\nvoid loop() {\n  digitalWrite(8, LOW); delayMicroseconds(2);\n  digitalWrite(8, HIGH); delayMicroseconds(10);\n  digitalWrite(8, LOW);\n  duration = pulseIn(9, HIGH);\n  distance = duration * 0.034 / 2;\n  Serial.print(\"Distance: \"); Serial.print(distance); Serial.println(\" cm\");\n  delay(200);\n}"
      }
    }
  },
  {
    "id": "mod-34",
    "number": "34",
    "name": "HXS 18650 11.1V 3S Li-ion Battery Pack",
    "category": "power",
    "tags": [
      "Power",
      "18650",
      "Battery",
      "11.1V"
    ],
    "images": [
      "assets/inventory/034_HXS_18650_11V1_Battery_Pack.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "HXS 18650 11.1V 3S 大容量鋰電池組",
        "desc": "專為智慧小車與機械臂馬達驅動設計的高倍率 11.1V (3S) 18650 鋰電池組，配備標準 DC5.5 電源接頭與保護板。",
        "specs": [
          {
            "label": "額定電壓",
            "val": "11.1V (飽和電壓 12.6V)"
          },
          {
            "label": "電池組合",
            "val": "3S 18650 串聯結構"
          },
          {
            "label": "輸出接頭",
            "val": "DC 5.5/2.1mm 公頭"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "DC Jack",
            "conn": "連接 Arduino VIN / 步進馬達驅動板 VMOT 電源"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "DC Jack",
            "conn": "經過 LM2596 / MP1584 降壓至 5V 後供電給 STM32"
          }
        ],
        "codeSnippet": "// 建議搭配電壓分壓電路監控電池剩餘電量"
      },
      "en": {
        "title": "HXS 18650 11.1V 3S Li-ion Battery Pack",
        "desc": "High-capacity 11.1V (3S) 18650 lithium battery pack designed for robot cars and motor drivers. Includes protection board and standard DC5.5 barrel connector.",
        "specs": [
          {
            "label": "Nominal Voltage",
            "val": "11.1V (Full charge 12.6V)"
          },
          {
            "label": "Cell Array",
            "val": "3S 18650 Series"
          },
          {
            "label": "Plug",
            "val": "DC 5.5/2.1mm Male Plug"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "DC Jack",
            "conn": "Connect to Arduino VIN / Stepper Driver VMOT"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "DC Jack",
            "conn": "Step down to 5V via LM2596/MP1584 before supplying STM32"
          }
        ],
        "codeSnippet": "// Voltage divider recommended for battery monitoring"
      }
    }
  },
  {
    "id": "mod-35",
    "number": "35",
    "name": "MCUZONE MPS2242 M.2 NVMe HAT",
    "category": "power",
    "tags": [
      "RaspberryPi",
      "NVMe",
      "PCIe",
      "SSD"
    ],
    "images": [
      "assets/inventory/035_Mcuzone_MPS2242_M2_NVMe_HAT_SSD.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "MCUZONE MPS2242 M.2 NVMe 固態硬碟擴充板",
        "desc": "適用於 Raspberry Pi 5 PCIe 介面的 M.2 NVMe 2242 固態硬碟擴充板，可大幅提升系統開機速度與檔案讀寫效能。",
        "specs": [
          {
            "label": "匯流排介面",
            "val": "PCIe Gen2 / Gen3 (透過 16-pin FPC 排線)"
          },
          {
            "label": "支援規格",
            "val": "M.2 Key-M 2242 尺寸 NVMe SSD"
          }
        ],
        "arduinoWiring": [],
        "stm32Wiring": [],
        "codeSnippet": "# Raspberry Pi 5 config.txt 啟用 PCIe Gen3 語法\ndtparam=pciex1\ndtparam=pciex1_no_max_payload_size\n# 啟用 PCIe 3.0 速度\ndtparam=pciex1_gen=3"
      },
      "en": {
        "title": "MCUZONE MPS2242 M.2 NVMe HAT",
        "desc": "M.2 NVMe SSD expansion board for Raspberry Pi 5 PCIe interface. Dramatically boosts boot speeds and file read/write performance.",
        "specs": [
          {
            "label": "Bus Interface",
            "val": "PCIe Gen2 / Gen3 (via 16-pin FPC cable)"
          },
          {
            "label": "Supported Drive",
            "val": "M.2 Key-M 2242 NVMe SSD"
          }
        ],
        "arduinoWiring": [],
        "stm32Wiring": [],
        "codeSnippet": "# Enable PCIe Gen3 in Raspberry Pi config.txt\ndtparam=pciex1\ndtparam=pciex1_no_max_payload_size\ndtparam=pciex1_gen=3"
      }
    }
  },
  {
    "id": "mod-36",
    "number": "36/37",
    "name": "Binocular Stereo Vision Camera Module",
    "category": "sensors",
    "tags": [
      "Sensors",
      "Camera",
      "StereoVision",
      "OpenCV"
    ],
    "images": [
      "assets/inventory/036_Binocular_Stereo_Camera_Module_Angle.jpg",
      "assets/inventory/037_Binocular_Stereo_Camera_Module_Front.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "雙目視覺立體深度感測攝影機模組",
        "desc": "具備雙同步光學鏡頭的立體相機模組，用於計算環境深度圖 (Depth Map)、3D 空間定位與人臉追蹤。",
        "specs": [
          {
            "label": "感光元件",
            "val": "雙重全時同步 CMOS"
          },
          {
            "label": "輸出介面",
            "val": "USB 2.0 免驅動 (UVC)"
          },
          {
            "label": "最高解析度",
            "val": "2560x720 60fps / 1280x480 60fps"
          }
        ],
        "arduinoWiring": [],
        "stm32Wiring": [],
        "codeSnippet": "# Python OpenCV 雙目視覺影像擷取\nimport cv2\ncap = cv2.VideoCapture(0)\ncap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)\ncap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)\nwhile True:\n    ret, frame = cap.read()\n    left_img = frame[:, :1280]\n    right_img = frame[:, 1280:]\n    cv2.imshow(\"Left\", left_img)\n    if cv2.waitKey(1) == 27: break"
      },
      "en": {
        "title": "Binocular Stereo Vision Camera Module",
        "desc": "Dual-lens stereo camera module for 3D depth map computation, spatial positioning, and AI object tracking.",
        "specs": [
          {
            "label": "Sensors",
            "val": "Dual Synchronized CMOS Sensors"
          },
          {
            "label": "Interface",
            "val": "USB 2.0 Driverless (UVC)"
          },
          {
            "label": "Max Resolution",
            "val": "2560x720 60fps / 1280x480 60fps"
          }
        ],
        "arduinoWiring": [],
        "stm32Wiring": [],
        "codeSnippet": "# Python OpenCV Stereo Capture\nimport cv2\ncap = cv2.VideoCapture(0)\ncap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)\ncap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)\nwhile True:\n    ret, frame = cap.read()\n    left_img = frame[:, :1280]\n    right_img = frame[:, 1280:]\n    cv2.imshow(\"Left\", left_img)\n    if cv2.waitKey(1) == 27: break"
      }
    }
  },
  {
    "id": "mod-45",
    "number": "45/46",
    "name": "HW-131 Breadboard Power Supply Module",
    "category": "power",
    "tags": [
      "Power",
      "Breadboard",
      "5V",
      "3.3V"
    ],
    "images": [
      "assets/inventory/045_HW131_Breadboard_Power_Supply_Front.jpg",
      "assets/inventory/046_HW131_Breadboard_Power_Supply_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "HW-131 雙路麵包板電源模組",
        "desc": "可直接插在標準 MB-102 麵包板兩側的獨立雙路電源模組，支援 5V / 3.3V 切換，方便為電路提供穩定的電壓輸出。",
        "specs": [
          {
            "label": "輸入電壓",
            "val": "DC 6.5V - 12V (DC接頭) 或 USB 5V"
          },
          {
            "label": "輸出電壓",
            "val": "3.3V / 5V 兩路獨立開關選擇"
          },
          {
            "label": "最大電流",
            "val": "< 700 mA"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Output Header",
            "conn": "直接插在麵包板電源正負軌"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Output Header",
            "conn": "提供 3.3V 給 STM32，5V 給周邊感測器"
          }
        ],
        "codeSnippet": "// 硬體模組，無需編寫程式"
      },
      "en": {
        "title": "HW-131 Breadboard Power Supply Module",
        "desc": "Plug-and-play power supply module for standard MB-102 breadboards. Provides independent 5V and 3.3V voltage rails.",
        "specs": [
          {
            "label": "Input Voltage",
            "val": "DC 6.5V - 12V (Barrel jack) or USB 5V"
          },
          {
            "label": "Output Voltage",
            "val": "3.3V / 5V dual rail toggles"
          },
          {
            "label": "Max Output Current",
            "val": "< 700 mA"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Output Header",
            "conn": "Plugs directly into breadboard power rails"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Output Header",
            "conn": "Supplies 3.3V to STM32, 5V to sensors"
          }
        ],
        "codeSnippet": "// Pure hardware power module"
      }
    }
  },
  {
    "id": "mod-47",
    "number": "47/49",
    "name": "MT8870 DTMF Audio Decoder Module",
    "category": "display_audio",
    "tags": [
      "Audio",
      "DTMF",
      "Decoder",
      "MT8870"
    ],
    "images": [
      "assets/inventory/047_MT8870_DTMF_Audio_Decoder_Top.jpg",
      "assets/inventory/049_MT8870_DTMF_Audio_Decoder_CloseUp.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "MT8870 雙音多頻 (DTMF) 音訊解碼模組",
        "desc": "透過 3.5mm 音訊孔接收電話按鍵雙音多頻 (DTMF) 訊號，並將解碼後的按鍵數值以 4-bit BCD 二進位碼與 StD 有效訊號 Pin 腳輸出。",
        "specs": [
          {
            "label": "晶片",
            "val": "MT8870D"
          },
          {
            "label": "輸入端子",
            "val": "3.5mm Audio Jack"
          },
          {
            "label": "輸出Pin腳",
            "val": "Q1, Q2, Q3, Q4 (BCD 數據), StD (解碼有效觸發標誌)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Q1-Q4",
            "conn": "Arduino D2, D3, D4, D5"
          },
          {
            "pin": "StD",
            "conn": "Arduino D6 (Interrupt 或 polling)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Q1-Q4",
            "conn": "STM32 PB0, PB1, PB2, PB3"
          },
          {
            "pin": "StD",
            "conn": "STM32 PB4"
          }
        ],
        "codeSnippet": "// Arduino MT8870 讀取範例\nvoid setup() {\n  for(int i=2; i<=6; i++) pinMode(i, INPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  if(digitalRead(6) == HIGH) { // StD 有效訊號\n    int code = (digitalRead(5)<<3) | (digitalRead(4)<<2) | (digitalRead(3)<<1) | digitalRead(2);\n    Serial.print(\"DTMF Key Code: \"); Serial.println(code);\n    delay(250);\n  }\n}"
      },
      "en": {
        "title": "MT8870 DTMF Audio Decoder Module",
        "desc": "Decodes telephone touch-tone (DTMF) audio signals received via 3.5mm jack into 4-bit BCD binary data outputs and StD valid signal flag.",
        "specs": [
          {
            "label": "IC",
            "val": "MT8870D"
          },
          {
            "label": "Input",
            "val": "3.5mm Audio Jack"
          },
          {
            "label": "Outputs",
            "val": "Q1, Q2, Q3, Q4 (BCD Data), StD (Valid Tone Flag)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Q1-Q4",
            "conn": "Arduino D2, D3, D4, D5"
          },
          {
            "pin": "StD",
            "conn": "Arduino D6 (Interrupt or polling)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Q1-Q4",
            "conn": "STM32 PB0, PB1, PB2, PB3"
          },
          {
            "pin": "StD",
            "conn": "STM32 PB4"
          }
        ],
        "codeSnippet": "// Arduino MT8870 Decoder Code\nvoid setup() {\n  for(int i=2; i<=6; i++) pinMode(i, INPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  if(digitalRead(6) == HIGH) { // StD valid signal\n    int code = (digitalRead(5)<<3) | (digitalRead(4)<<2) | (digitalRead(3)<<1) | digitalRead(2);\n    Serial.print(\"DTMF Key Code: \"); Serial.println(code);\n    delay(250);\n  }\n}"
      }
    }
  },
  {
    "id": "mod-50",
    "number": "50/51/61/62",
    "name": "IR Obstacle Avoidance Sensor Module",
    "category": "sensors",
    "tags": [
      "Sensors",
      "Infrared",
      "Obstacle",
      "Proximity"
    ],
    "images": [
      "assets/inventory/050_IR_Obstacle_Sensor_Board1_Back.jpg",
      "assets/inventory/051_IR_Obstacle_Sensor_Board1_Front.jpg",
      "assets/inventory/061_IR_Obstacle_Sensor_Board2_Front.jpg",
      "assets/inventory/062_IR_Obstacle_Sensor_Board2_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "紅外線障礙物避障感測器模組",
        "desc": "紅外線發射與接收對管模組，發射一定頻率的紅外線，遇到障礙物反射回接收管，經比較器解算輸出低電位致能訊號。",
        "specs": [
          {
            "label": "感測距離",
            "val": "2cm - 30cm (透過板載精密電位器可調)"
          },
          {
            "label": "感測角度",
            "val": "35° 錐形區域"
          },
          {
            "label": "輸出電位",
            "val": "數位 OUT (有障礙物輸出 LOW，無障礙物輸出 HIGH)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 5V"
          },
          {
            "pin": "GND",
            "conn": "Arduino GND"
          },
          {
            "pin": "OUT",
            "conn": "Arduino D2"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "OUT",
            "conn": "STM32 PA0 (EXTI0 中斷輸入)"
          }
        ],
        "codeSnippet": "void setup() {\n  pinMode(2, INPUT);\n  pinMode(13, OUTPUT);\n}\nvoid loop() {\n  if (digitalRead(2) == LOW) { // 遇到障礙物\n    digitalWrite(13, HIGH);\n  } else {\n    digitalWrite(13, LOW);\n  }\n}"
      },
      "en": {
        "title": "IR Obstacle Avoidance Sensor Module",
        "desc": "Active IR proximity detection module. Emits modulated IR light and detects reflections from nearby objects, outputting an active-low digital signal.",
        "specs": [
          {
            "label": "Detection Range",
            "val": "2cm - 30cm (Adjustable via onboard potentiometer)"
          },
          {
            "label": "Detection Angle",
            "val": "35° Cone"
          },
          {
            "label": "Output Voltage",
            "val": "Digital OUT (LOW when object detected, HIGH otherwise)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 5V"
          },
          {
            "pin": "GND",
            "conn": "Arduino GND"
          },
          {
            "pin": "OUT",
            "conn": "Arduino D2"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "OUT",
            "conn": "STM32 PA0 (EXTI0 Interrupt Input)"
          }
        ],
        "codeSnippet": "void setup() {\n  pinMode(2, INPUT);\n  pinMode(13, OUTPUT);\n}\nvoid loop() {\n  if (digitalRead(2) == LOW) { // Obstacle detected\n    digitalWrite(13, HIGH);\n  } else {\n    digitalWrite(13, LOW);\n  }\n}"
      }
    }
  },
  {
    "id": "mod-52",
    "number": "52/53",
    "name": "XH-M229 PC ATX Power Supply Breakout",
    "category": "power",
    "tags": [
      "Power",
      "ATX",
      "12V",
      "5V",
      "3.3V"
    ],
    "images": [
      "assets/inventory/052_XH_M229_ATX_Power_Breakout_Front.jpg",
      "assets/inventory/053_XH_M229_ATX_Power_Breakout_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "XH-M229 桌上型電腦 ATX 電源轉接輸出板",
        "desc": "可將標準 PC 24-pin ATX 電源轉接為實驗室多路直流穩壓電源的擴充板，具備開關切換與獨立保險絲端子。",
        "specs": [
          {
            "label": "輸入插座",
            "val": "24-pin Standard ATX Power Supply"
          },
          {
            "label": "輸出電壓軌",
            "val": "+3.3V, +5V, +12V, -12V 獨立輸出"
          },
          {
            "label": "安全保護",
            "val": "每組輸出均板載金屬保險絲與螺絲端子"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "+5V / GND",
            "conn": "提供大電流給伺服馬達與 Arduino"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "+3.3V / GND",
            "conn": "提供穩壓電壓給 STM32 開發板"
          }
        ],
        "codeSnippet": "// 硬體電源轉換板"
      },
      "en": {
        "title": "XH-M229 PC ATX Power Supply Breakout",
        "desc": "Breakout board converting standard desktop PC 24-pin ATX power supplies into multi-rail lab bench power supplies with onboard toggle switch and fuses.",
        "specs": [
          {
            "label": "Input Port",
            "val": "24-pin Standard ATX Power Supply"
          },
          {
            "label": "Output Rails",
            "val": "+3.3V, +5V, +12V, -12V DC"
          },
          {
            "label": "Protection",
            "val": "Glass fuse & screw terminals on each output line"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "+5V / GND",
            "conn": "High-current power for servos & Arduino"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "+3.3V / GND",
            "conn": "Stable regulated supply for STM32 board"
          }
        ],
        "codeSnippet": "// Pure hardware power adapter"
      }
    }
  },
  {
    "id": "mod-58",
    "number": "58",
    "name": "Waveshare USB to TTL Serial Adapter",
    "category": "power",
    "tags": [
      "Power",
      "USB",
      "TTL",
      "Serial",
      "FT232"
    ],
    "images": [
      "assets/inventory/058_Waveshare_USB_to_TTL_Adapter.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "Waveshare USB 轉 TTL 序列埠轉接器",
        "desc": "用於微控制器、樹莓派及開發板主機除錯與 Serial 訊號傳輸的 USB 轉 TTL 轉接模組，支援 3.3V/5V 電位切換。",
        "specs": [
          {
            "label": "通訊晶片",
            "val": "FT232 / CH340 Industrial Serial Chip"
          },
          {
            "label": "腳位輸出",
            "val": "VCC, GND, TXD, RXD, RTS, CTS"
          },
          {
            "label": "邏輯電位",
            "val": "可透過 Jumper 切換 3.3V / 5V"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "TXD -> RX",
            "conn": "RXD -> TX, GND -> GND"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "TXD -> PA10 (RX)",
            "conn": "RXD -> PA9 (TX), GND -> GND"
          }
        ],
        "codeSnippet": "// 用於傳輸 Serial.print() 資訊"
      },
      "en": {
        "title": "Waveshare USB to TTL Serial Adapter",
        "desc": "Industrial USB to TTL UART serial converter adapter used for microcontrollers, Raspberry Pi console debugging, and serial data transmission.",
        "specs": [
          {
            "label": "Serial IC",
            "val": "FT232 / CH340 Industrial USB-Serial IC"
          },
          {
            "label": "Pinout",
            "val": "VCC, GND, TXD, RXD, RTS, CTS"
          },
          {
            "label": "Voltage Level",
            "val": "3.3V / 5V selectable via jumper"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "TXD -> RX",
            "conn": "RXD -> TX, GND -> GND"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "TXD -> PA10 (RX)",
            "conn": "RXD -> PA9 (TX), GND -> GND"
          }
        ],
        "codeSnippet": "// Serial.print() Debug Interface"
      }
    }
  },
  {
    "id": "mod-59",
    "number": "59/60",
    "name": "A4988 Stepper Motor Driver Module",
    "category": "motion",
    "tags": [
      "Motion",
      "A4988",
      "Stepper",
      "Driver"
    ],
    "images": [
      "assets/inventory/059_A4988_Stepper_Motor_Driver_Front.jpg",
      "assets/inventory/060_A4988_Stepper_Motor_Driver_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "A4988 步進馬達微步驅動模組",
        "desc": "廣泛應用於 3D 列印機與 CNC 雕刻機的兩相四線步進馬達驅動晶片，支援全步至 1/16 微步控制與可調限流。",
        "specs": [
          {
            "label": "馬達供電",
            "val": "8V - 35V DC"
          },
          {
            "label": "最大電流",
            "val": "2A (需加裝散熱片與風扇)"
          },
          {
            "label": "細分模式",
            "val": "全步, 1/2, 1/4, 1/8, 1/16 微步 (MS1, MS2, MS3 設定)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "STEP",
            "conn": "Arduino D2"
          },
          {
            "pin": "DIR",
            "conn": "Arduino D3"
          },
          {
            "pin": "ENABLE",
            "conn": "Arduino D4"
          },
          {
            "pin": "1A, 1B, 2A, 2B",
            "conn": "步进马达四线"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "STEP",
            "conn": "STM32 PA0"
          },
          {
            "pin": "DIR",
            "conn": "STM32 PA1"
          }
        ],
        "codeSnippet": "void setup() {\n  pinMode(2, OUTPUT); // STEP\n  pinMode(3, OUTPUT); // DIR\n}\nvoid loop() {\n  digitalWrite(3, HIGH); // 正轉\n  for(int i=0; i<200; i++) { // 旋轉一圈 (200步)\n    digitalWrite(2, HIGH); delayMicroseconds(800);\n    digitalWrite(2, LOW);  delayMicroseconds(800);\n  }\n  delay(1000);\n}"
      },
      "en": {
        "title": "A4988 Stepper Motor Driver Module",
        "desc": "Microstepping driver for bipolar stepper motors used in 3D printers and CNC machines. Features adjustable current limiting and 5 microstep resolutions down to 1/16.",
        "specs": [
          {
            "label": "Motor Voltage",
            "val": "8V - 35V DC"
          },
          {
            "label": "Max Current",
            "val": "2A (Heatsink & active cooling required)"
          },
          {
            "label": "Microsteps",
            "val": "Full, 1/2, 1/4, 1/8, 1/16 step (MS1, MS2, MS3 pins)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "STEP",
            "conn": "Arduino D2"
          },
          {
            "pin": "DIR",
            "conn": "Arduino D3"
          },
          {
            "pin": "ENABLE",
            "conn": "Arduino D4"
          },
          {
            "pin": "1A, 1B, 2A, 2B",
            "conn": "Stepper Motor 4 Wires"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "STEP",
            "conn": "STM32 PA0"
          },
          {
            "pin": "DIR",
            "conn": "STM32 PA1"
          }
        ],
        "codeSnippet": "void setup() {\n  pinMode(2, OUTPUT); // STEP\n  pinMode(3, OUTPUT); // DIR\n}\nvoid loop() {\n  digitalWrite(3, HIGH); // Forward\n  for(int i=0; i<200; i++) { // 1 Revolution (200 steps)\n    digitalWrite(2, HIGH); delayMicroseconds(800);\n    digitalWrite(2, LOW);  delayMicroseconds(800);\n  }\n  delay(1000);\n}"
      }
    }
  },
  {
    "id": "mod-63",
    "number": "63/64",
    "name": "Optocoupler Speed Sensor Module",
    "category": "sensors",
    "tags": [
      "Sensors",
      "Speed",
      "RPM",
      "Encoder",
      "LM393"
    ],
    "images": [
      "assets/inventory/063_Speed_Sensor_Module_Front.jpg",
      "assets/inventory/064_Speed_Sensor_Module_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "槽型光電過光測速與轉速計感測器模組",
        "desc": "採用 5mm 槽寬紅外線過光光電斷續器，搭配小車碼盤可精算輪胎轉速 (RPM) 與移動距離。",
        "specs": [
          {
            "label": "槽寬距離",
            "val": "5 mm"
          },
          {
            "label": "比較器晶片",
            "val": "LM393 寬電壓比較器"
          },
          {
            "label": "輸出訊號",
            "val": "數位 DO (過光脈衝) 與類比 AO"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "5V"
          },
          {
            "pin": "GND",
            "conn": "GND"
          },
          {
            "pin": "OUT",
            "conn": "Arduino D2 (External Interrupt 0)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "OUT",
            "conn": "STM32 PA0 (TIM2 Input Capture)"
          }
        ],
        "codeSnippet": "volatile unsigned int pulses = 0;\nvoid countPulse() { pulses++; }\nvoid setup() {\n  attachInterrupt(digitalPinToInterrupt(2), countPulse, RISING);\n  Serial.begin(9600);\n}\nvoid loop() {\n  delay(1000);\n  Serial.print(\"Pulses per sec: \"); Serial.println(pulses);\n  pulses = 0;\n}"
      },
      "en": {
        "title": "Optocoupler Speed Sensor Module",
        "desc": "Optocoupler speed counter module with 5mm slot width. Combined with encoder discs to measure wheel rotation RPM and distance.",
        "specs": [
          {
            "label": "Slot Width",
            "val": "5 mm"
          },
          {
            "label": "Comparator IC",
            "val": "LM393 Wide Voltage Comparator"
          },
          {
            "label": "Output",
            "val": "Digital DO (Pulse output) and Analog AO"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "5V"
          },
          {
            "pin": "GND",
            "conn": "GND"
          },
          {
            "pin": "OUT",
            "conn": "Arduino D2 (External Interrupt 0)"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "OUT",
            "conn": "STM32 PA0 (TIM2 Input Capture)"
          }
        ],
        "codeSnippet": "volatile unsigned int pulses = 0;\nvoid countPulse() { pulses++; }\nvoid setup() {\n  attachInterrupt(digitalPinToInterrupt(2), countPulse, RISING);\n  Serial.begin(9600);\n}\nvoid loop() {\n  delay(1000);\n  Serial.print(\"Pulses per sec: \"); Serial.println(pulses);\n  pulses = 0;\n}"
      }
    }
  },
  {
    "id": "mod-68",
    "number": "68/69",
    "name": "YourFun NRF24L01 2.4GHz Wireless Module",
    "category": "power",
    "tags": [
      "Wireless",
      "NRF24L01",
      "2.4GHz",
      "SPI"
    ],
    "images": [
      "assets/inventory/068_YourFun_Robotics_Wireless_Module_Pinout.jpg",
      "assets/inventory/069_YourFun_Robotics_Wireless_Module_Top.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "越凡 NRF24L01 2.4GHz 射頻無線通訊模組",
        "desc": "高可靠度 2.4GHz ISM 頻段無線收發模組，用於機器人遙控器與小車之間的低延遲無線資料傳送。",
        "specs": [
          {
            "label": "工作頻率",
            "val": "2.4GHz - 2.5GHz"
          },
          {
            "label": "通訊介面",
            "val": "Standard SPI Protocol"
          },
          {
            "label": "供電電壓",
            "val": "1.9V - 3.6V (切勿接 5V，容易燒毀)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 3.3V"
          },
          {
            "pin": "CE",
            "conn": "D9"
          },
          {
            "pin": "CSN",
            "conn": "D10"
          },
          {
            "pin": "SCK/MOSI/MISO",
            "conn": "D13/D11/D12"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "SPI1 Pins",
            "conn": "STM32 PA4(CSN), PA5(SCK), PA6(MISO), PA7(MOSI)"
          }
        ],
        "codeSnippet": "// Arduino RF24 無線發送範例\n#include <SPI.h>\n#include <RF24.h>\nRF24 radio(9, 10);\nconst byte address[6] = \"00001\";\nvoid setup() {\n  radio.begin();\n  radio.openWritingPipe(address);\n  radio.stopListening();\n}\nvoid loop() {\n  const char text[] = \"Hello Robot\";\n  radio.write(&text, sizeof(text));\n  delay(1000);\n}"
      },
      "en": {
        "title": "YourFun NRF24L01 2.4GHz Wireless Module",
        "desc": "2.4GHz ISM band RF transceiver module for low-latency wireless communication between remote controllers and robot cars.",
        "specs": [
          {
            "label": "Frequency Band",
            "val": "2.4GHz - 2.5GHz"
          },
          {
            "label": "Protocol",
            "val": "Standard SPI Interface"
          },
          {
            "label": "Operating Voltage",
            "val": "1.9V - 3.6V (Do NOT connect 5V directly!)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "VCC",
            "conn": "Arduino 3.3V"
          },
          {
            "pin": "CE",
            "conn": "D9"
          },
          {
            "pin": "CSN",
            "conn": "D10"
          },
          {
            "pin": "SCK/MOSI/MISO",
            "conn": "D13/D11/D12"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "SPI1 Pins",
            "conn": "STM32 PA4(CSN), PA5(SCK), PA6(MISO), PA7(MOSI)"
          }
        ],
        "codeSnippet": "// Arduino RF24 Transmit Code\n#include <SPI.h>\n#include <RF24.h>\nRF24 radio(9, 10);\nconst byte address[6] = \"00001\";\nvoid setup() {\n  radio.begin();\n  radio.openWritingPipe(address);\n  radio.stopListening();\n}\nvoid loop() {\n  const char text[] = \"Hello Robot\";\n  radio.write(&text, sizeof(text));\n  delay(1000);\n}"
      }
    }
  },
  {
    "id": "mod-70",
    "number": "70/71",
    "name": "Waveshare PCA9685 Servo Driver HAT",
    "category": "motion",
    "tags": [
      "Motion",
      "PCA9685",
      "PWM",
      "Servo",
      "I2C"
    ],
    "images": [
      "assets/inventory/070_Waveshare_PCA9685_Servo_Driver_HAT_Front.jpg",
      "assets/inventory/071_Waveshare_PCA9685_Servo_Driver_HAT_Back.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "Waveshare 16路 12位元 PWM 伺服馬達驅動板",
        "desc": "提供 16 通道獨立 12-bit 解析度 PWM 脈衝輸出的驅動擴充板，一次可控制多達 16 組多關節機械臂舵機。",
        "specs": [
          {
            "label": "控制通道",
            "val": "16 路獨立 PWM 輸出"
          },
          {
            "label": "解析度",
            "val": "12-bit (4096 階解析度)"
          },
          {
            "label": "輸入介面",
            "val": "I2C (最高支援 62 個模組串聯級聯)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "SDA/SCL",
            "conn": "Arduino A4 / A5"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "SDA/SCL",
            "conn": "STM32 PB7 / PB6"
          }
        ],
        "codeSnippet": "// 搭配 Adafruit PWM Library 控制多足機器人"
      },
      "en": {
        "title": "Waveshare PCA9685 Servo Driver HAT",
        "desc": "16-Channel 12-Bit PWM servo driver expansion board over I2C. Controls up to 16 robotic arm servos simultaneously.",
        "specs": [
          {
            "label": "Channels",
            "val": "16 Independent PWM Channels"
          },
          {
            "label": "Resolution",
            "val": "12-bit (4096 Steps)"
          },
          {
            "label": "Interface",
            "val": "I2C (Supports up to 62 boards cascaded)"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "SDA/SCL",
            "conn": "Arduino A4 / A5"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "SDA/SCL",
            "conn": "STM32 PB7 / PB6"
          }
        ],
        "codeSnippet": "// Pair with Adafruit PWM Servo Driver Library"
      }
    }
  },
  {
    "id": "mod-82",
    "number": "82",
    "name": "Waterproof Metal Push Button Switches",
    "category": "display_audio",
    "tags": [
      "Interface",
      "Switch",
      "Button",
      "LED"
    ],
    "images": [
      "assets/inventory/082_Waterproof_Metal_Push_Button_Switches.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "金屬防暴防水電源帶燈按鈕開關組",
        "desc": "高質感金屬防潮按鈕開關，內建環形 LED 指示燈，適合安裝在機器人機殼作為主電源切換或緊急停止按鍵。",
        "specs": [
          {
            "label": "觸點類型",
            "val": "1NO1NC (一常開一常閉) / 自鎖按鈕"
          },
          {
            "label": "LED 電壓",
            "val": "12V / 5V 環形指示燈"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Switch",
            "conn": "控制 VIN 電源線路"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Switch",
            "conn": "控制 電源繼電器通斷"
          }
        ],
        "codeSnippet": "// 硬體電源開關組"
      },
      "en": {
        "title": "Waterproof Metal Push Button Switches",
        "desc": "Heavy-duty waterproof metal push button switch with ring LED indicator for robot chassis power toggle or emergency stop.",
        "specs": [
          {
            "label": "Contact Type",
            "val": "1NO1NC (1 Normally Open, 1 Normally Closed) / Latching"
          },
          {
            "label": "Ring LED Voltage",
            "val": "12V / 5V Ring LED"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Switch",
            "conn": "Controls main VIN power rail"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Switch",
            "conn": "Triggers main power relay"
          }
        ],
        "codeSnippet": "// Pure Hardware Power Switch"
      }
    }
  },
  {
    "id": "mod-83",
    "number": "83/84/85",
    "name": "Waveshare MG996R / MG90S / SG90 Servos",
    "category": "motion",
    "tags": [
      "Motion",
      "Servo",
      "MG996R",
      "MG90S",
      "SG90"
    ],
    "images": [
      "assets/inventory/083_Waveshare_MG996R_Servo_Motor.jpg",
      "assets/inventory/084_Waveshare_MG90S_Micro_Servos_Set.jpg",
      "assets/inventory/085_Waveshare_SG90_Micro_Servo.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "Waveshare 大扭力金屬舵機與微型伺服馬達組",
        "desc": "機械臂與雲台的核心致動器組，包含大扭力金屬齒輪舵機 MG996R (11kg/cm)、金屬微型舵機 MG90S (2.2kg/cm) 與輕量 SG90。",
        "specs": [
          {
            "label": "MG996R",
            "val": "工作電壓 4.8V-7.2V, 扭力 11kg/cm, 全金屬齒輪"
          },
          {
            "label": "MG90S",
            "val": "工作電壓 4.8V-6V, 扭力 2.2kg/cm, 金屬齒輪"
          },
          {
            "label": "SG90",
            "val": "工作電壓 4.8V, 重量 9g, 塑膠齒輪"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Signal (黃/橘)",
            "conn": "Arduino PWM 引腳 (例如 D9, D10)"
          },
          {
            "pin": "VCC (紅)",
            "conn": "外部 5V-6V 電源"
          },
          {
            "pin": "GND (棕/黑)",
            "conn": "GND"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Signal",
            "conn": "STM32 TIM2 / TIM3 PWM 頻道引腳"
          }
        ],
        "codeSnippet": "#include <Servo.h>\nServo myServo;\nvoid setup() {\n  myServo.attach(9);\n}\nvoid loop() {\n  myServo.write(0); delay(1000);\n  myServo.write(90); delay(1000);\n  myServo.write(180); delay(1000);\n}"
      },
      "en": {
        "title": "Waveshare MG996R / MG90S / SG90 Servos",
        "desc": "Essential servo actuators for robotic arms and pan-tilts, including high-torque metal gear MG996R (11kg/cm), micro metal gear MG90S (2.2kg/cm), and lightweight SG90.",
        "specs": [
          {
            "label": "MG996R",
            "val": "4.8V-7.2V, Torque 11kg/cm, Full Metal Gear"
          },
          {
            "label": "MG90S",
            "val": "4.8V-6V, Torque 2.2kg/cm, Metal Gear"
          },
          {
            "label": "SG90",
            "val": "4.8V, 9g weight, Plastic Gear"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Signal (Yellow/Orange)",
            "conn": "Arduino PWM Pin (e.g. D9, D10)"
          },
          {
            "pin": "VCC (Red)",
            "conn": "External 5V-6V Supply"
          },
          {
            "pin": "GND (Brown/Black)",
            "conn": "GND"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Signal",
            "conn": "STM32 TIM2 / TIM3 PWM Channel Pin"
          }
        ],
        "codeSnippet": "#include <Servo.h>\nServo myServo;\nvoid setup() {\n  myServo.attach(9);\n}\nvoid loop() {\n  myServo.write(0); delay(1000);\n  myServo.write(90); delay(1000);\n  myServo.write(180); delay(1000);\n}"
      }
    }
  },
  {
    "id": "mod-90",
    "number": "90/22/23",
    "name": "37-in-1 Sensor Modules Reference Guide",
    "category": "kit37",
    "tags": [
      "Kit",
      "Sensors",
      "37in1",
      "Arduino"
    ],
    "images": [
      "assets/inventory/090_SensorKit_37in1_Reference_Guide_Sheet.jpg",
      "assets/inventory/022_SensorKit_37in1_Diagram_Chart.jpg",
      "assets/inventory/023_SensorKit_37in1_Module_Box.jpg"
    ],
    "i18n": {
      "zh": {
        "title": "37合1 基礎感測器模組參考圖表與套裝",
        "desc": "包含完整 37 種開源硬體基礎感測器（火焰、光敏、震動、聲音、繼電器、磁簧、水銀、RGB、蜂鳴器、溫度等）的完整清單與說明圖表。",
        "specs": [
          {
            "label": "收錄感測器",
            "val": "DS18B20、DHT11、MPU6050、HC-SR04、火焰、光敏、繼電器等 37 種"
          },
          {
            "label": "工作電壓",
            "val": "通用 3.3V - 5V"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Pinout",
            "conn": "請點擊各個別模組查詢專屬腳位圖"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Pinout",
            "conn": "請點擊各個別模組查詢專屬腳位圖"
          }
        ],
        "codeSnippet": "// 37合1 感測器庫合集範例"
      },
      "en": {
        "title": "37-in-1 Sensor Modules Reference Guide",
        "desc": "Complete reference manual and chart for the 37-in-1 open-source sensor kit (flame, photoresistor, vibration, sound, relay, hall, buzzer, temperature, etc.).",
        "specs": [
          {
            "label": "Included Modules",
            "val": "DS18B20, DHT11, MPU6050, HC-SR04, Flame, Relay, etc."
          },
          {
            "label": "Voltage",
            "val": "3.3V - 5V Universal"
          }
        ],
        "arduinoWiring": [
          {
            "pin": "Pinout",
            "conn": "See individual module details"
          }
        ],
        "stm32Wiring": [
          {
            "pin": "Pinout",
            "conn": "See individual module details"
          }
        ],
        "codeSnippet": "// 37-in-1 Sensor Library Collection"
      }
    }
  }
];

function buildModules(lang, assetBase = '') {
  return MODULES.map((m) => ({
    ...m,
    ...m.i18n[lang],
    images: m.images.map((p) => assetBase + p),
  }));
}
