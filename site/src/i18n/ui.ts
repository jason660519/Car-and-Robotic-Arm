export const LOCALES = ['zh', 'en'] as const;
export type Locale = (typeof LOCALES)[number];

export const ui = {
  zh: {
    'site.title': '丹尼的機器人與感測器模組庫',
    'site.subtitle': 'Danny 的小車 + 機械臂專案報告',
    'nav.home': '專案總覽',
    'nav.inventory': '零件庫存',
    'nav.assembly': '組裝指南',
    'nav.switch': 'English',
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
    'site.subtitle': 'Smart Car + Robotic Arm Project Report',
    'nav.home': 'Overview',
    'nav.inventory': 'Inventory',
    'nav.assembly': 'Assembly Guide',
    'nav.switch': '繁體中文',
    'inventory.title': 'Hardware & Sensor Module Inventory',
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
  const prefix = locale === 'en' ? '/en' : '';
  return `${base}${prefix}${clean ? `/${clean}` : ''}/`;
}
