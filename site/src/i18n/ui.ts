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
    'inventory.section.photos': '模組實體照片',
    'inventory.section.desc': '功能簡介與詳細說明',
    'inventory.section.specs': '規格與硬體參數',
    'inventory.section.arduino': 'Arduino 接線',
    'inventory.section.stm32': 'STM32 接線',
    'inventory.section.code': '程式範例',
    'inventory.wiring.pin': '腳位',
    'inventory.wiring.conn': '連接到',
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
    'inventory.section.photos': 'Module Photos',
    'inventory.section.desc': 'Overview & Details',
    'inventory.section.specs': 'Specifications',
    'inventory.section.arduino': 'Arduino Wiring',
    'inventory.section.stm32': 'STM32 Wiring',
    'inventory.section.code': 'Code Example',
    'inventory.wiring.pin': 'Pin',
    'inventory.wiring.conn': 'Connects to',
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
