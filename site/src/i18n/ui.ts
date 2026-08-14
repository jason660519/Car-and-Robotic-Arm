export const LOCALES = ['en', 'zh'] as const;
export type Locale = (typeof LOCALES)[number];

export const ui = {
  zh: {
    'site.title': '丹尼的機器人與感測器模組庫',
    'site.subtitle': 'Danny 的 Smart Car + Robotic 概念專案記錄',
    'nav.home': '專案總覽',
    'nav.inventory': '零件庫存',
    'nav.assembly': '組裝指南',
    'nav.switch': 'English',
    'home.eyebrow': 'Raspberry Pi 5 · NeZha I2C · Smart Car + Robotic',
    'home.title': 'Smart Car + Robotic 概念專案',
    'home.lede':
      '樹莓派透過 I2C 控制 NeZha 總線驅動板，驅動四顆馬達、四個舵機與板載燈效。這個網站收錄零件庫存、組裝步驟與硬體筆記。',
    'project.note':
      '並不是所有部件都會實際使用。專案可能因費用、軟硬體相容性或零件損壞而調整方向；目前整體仍以 Smart Car + Robotic 概念為主。',
    'inventory.title': '零件與感測器模組庫',
    'inventory.search': '搜尋模組名稱、晶片（例如：MPU6050, Servo, PCA9685, 超音波, 循跡）…',
    'inventory.count': '收錄模組',
    'inventory.unit': '項',
    'inventory.empty.title': '未找到符合條件的模組',
    'inventory.empty.desc': '請嘗試使用不同的搜尋關鍵字或切換分類標籤。',
    'inventory.photos': '張照片',
    'inventory.categories': '零件分類',
    'inventory.category.showing': '此分類顯示',
    'inventory.back': '← 返回分類',
    'inventory.section.photos': '模組實體照片',
    'inventory.section.desc': '功能簡介與詳細說明',
    'inventory.section.specs': '規格與硬體參數',
    'inventory.section.raspberryPi': 'Raspberry Pi 5 接線',
    'inventory.section.arduino': 'Arduino 接線',
    'inventory.section.stm32': 'STM32 接線',
    'inventory.section.code': '程式範例',
    'inventory.wiring.pin': '腳位',
    'inventory.wiring.conn': '連接到',
    'pinout.title': 'Raspberry Pi 5 GPIO 針腳圖',
    'pinout.lede':
      '40-pin 排針對照表，顏色代表功能分組。編號與板子實體位置一致：奇數在左排、偶數在右排，Pin 1 在最靠近 USB-C 電源孔的那一端。',
    'pinout.legend': '功能分組',
    'pinout.col.func': '功能',
    'pinout.col.pin': 'Pin',
    'pinout.nezha':
      'NeZha 驅動板的 IIC 接口（G / SDA / SCL / 5V）對應到圖上標記的三根：SDA → Pin 3、SCL → Pin 5、G → Pin 6。驅動板若已自行供電，5V 那條就不要接到 Pi，避免兩組電源對灌。',
    'pinout.warn':
      'GPIO 邏輯電平是 3.3V。不要把 5V 訊號直接接到訊號腳位，也不要把 5V 灌進 Pin 1 或 Pin 17。',
    'pinout.source': '資料來源',
    'pinout.source.doc': '專案硬體筆記',
    'pinout.source.official': 'Raspberry Pi 官方 GPIO 文件',
    'assembly.title': '大聖多形態小車 + 機械臂組裝指南',
    'lightbox.filename': '檔名',
  },
  en: {
    'site.title': "Danny's Hardware & Sensor Inventory",
    'site.subtitle': 'Smart Car + Robotic Concept Project Notes',
    'nav.home': 'Overview',
    'nav.inventory': 'My Inventory and Tools',
    'nav.assembly': 'Assembly Guide',
    'nav.switch': '繁體中文',
    'home.eyebrow': 'Raspberry Pi 5 · NeZha I2C · Smart Car + Robotic',
    'home.title': 'Smart Car + Robotic Concept Project',
    'home.lede':
      'A Raspberry Pi 5 drives the NeZha bus board over I2C - four motors, four servos and onboard lighting. This site collects the parts inventory, assembly steps and hardware notes.',
    'project.note':
      'Not every part in this inventory will be used in the final build. The project direction may change because of cost, hardware and software compatibility, or damaged parts, but the overall idea remains a Smart Car + Robotic concept.',
    'inventory.title': 'My Inventory and Tools',
    'inventory.search': 'Search modules or chips (e.g. MPU6050, Servo, PCA9685, Ultrasonic)…',
    'inventory.count': 'Modules',
    'inventory.unit': '',
    'inventory.empty.title': 'No modules matched',
    'inventory.empty.desc': 'Try a different keyword or switch category.',
    'inventory.photos': 'photos',
    'inventory.categories': 'Categories',
    'inventory.category.showing': 'Showing',
    'inventory.back': '← Back to category',
    'inventory.section.photos': 'Module Photos',
    'inventory.section.desc': 'Overview & Details',
    'inventory.section.specs': 'Specifications',
    'inventory.section.raspberryPi': 'Raspberry Pi 5 Wiring',
    'inventory.section.arduino': 'Arduino Wiring',
    'inventory.section.stm32': 'STM32 Wiring',
    'inventory.section.code': 'Code Example',
    'inventory.wiring.pin': 'Pin',
    'inventory.wiring.conn': 'Connects to',
    'pinout.title': 'Raspberry Pi 5 GPIO Pinout',
    'pinout.lede':
      'The 40-pin header, colour-coded by function. Numbering follows the physical board: odd pins in the left column, even pins in the right, with Pin 1 at the end nearest the USB-C power connector.',
    'pinout.legend': 'Function groups',
    'pinout.col.func': 'Function',
    'pinout.col.pin': 'Pin',
    'pinout.nezha':
      'The NeZha bus board IIC header (G / SDA / SCL / 5V) maps to the three marked pins: SDA to Pin 3, SCL to Pin 5, G to Pin 6. Leave the 5V wire off when the board already has its own supply, so two rails do not fight.',
    'pinout.warn':
      'GPIO logic is 3.3V. Never feed a 5V signal into a GPIO pin, and never feed 5V into Pin 1 or Pin 17.',
    'pinout.source': 'Sources',
    'pinout.source.doc': 'Project hardware notes',
    'pinout.source.official': 'Official Raspberry Pi GPIO documentation',
    'assembly.title': 'Dasheng Multi-Form Smart Car & Robotic Arm Assembly Guide',
    'lightbox.filename': 'Filename',
  },
} as const;

export function t(locale: Locale) {
  return (key: keyof (typeof ui)['zh']): string => ui[locale][key] ?? ui.zh[key];
}

/** 產生站內連結，自動加上 base 與語系前綴。 */
export function href(locale: Locale, path = ''): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const clean = path.replace(/^\/|\/$/g, '');
  const prefix = locale === 'zh' ? '/zh' : '';
  return `${base}${prefix}${clean ? `/${clean}` : ''}/`;
}
