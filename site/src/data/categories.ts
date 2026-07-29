/** 庫存頁的分類標籤。新增分類時 zh / en 都要補，否則會 fallback 成 key。 */
export const CATEGORIES = [
  { key: 'all', zh: '全部模組 (All)', en: 'All Modules' },
  { key: 'controllers', zh: '主控板 (Controllers)', en: 'Controllers & MCU' },
  { key: 'motion', zh: '運動驅動 (Motion & Servos)', en: 'Motion & Servo Drivers' },
  { key: 'sensors', zh: '感測器 & 視覺 (Sensors & Vision)', en: 'Sensors & Vision' },
  { key: 'display_audio', zh: '顯示與音訊 (Display & Audio)', en: 'Display & Audio' },
  { key: 'power', zh: '電源與擴充板 (Power & Adapters)', en: 'Power & Adapters' },
  { key: 'kit37', zh: '37合1模組套件 (37-in-1 Kit)', en: '37-in-1 Sensor Kit' },
] as const;
