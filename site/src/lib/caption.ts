import type { Locale } from '../i18n/ui';

/** 從檔名推斷照片類型說明，沿用原本 getImageCaption() 的判斷順序。 */
export function imageCaption(filename: string, locale: Locale): string {
  const rules: Array<[RegExp, string, string]> = [
    [/Front/, '📸 正面特寫與元件外觀 (Front View)', '📸 Front View & Components'],
    [/Back/, '🔍 背面電路與腳位絲印 (Back View & Pinouts)', '🔍 Back View & Pinout Labels'],
    [/Angle/, '📐 斜向 3D 立體視角 (Perspective View)', '📐 Perspective View'],
    [/CloseUp|Pinout/, '🔎 腳位與晶片細節特寫 (Pinout Detail)', '🔎 Pinout & Chip Detail'],
    [/Sheet|Chart|Diagram|Guide/, '📋 規格對照參考圖表 (Reference Chart)', '📋 Reference Chart'],
  ];
  for (const [re, zh, en] of rules) {
    if (re.test(filename)) return locale === 'zh' ? zh : en;
  }
  return locale === 'zh' ? '📷 模組實體照片 (Module Photo)' : '📷 Module Photo';
}
