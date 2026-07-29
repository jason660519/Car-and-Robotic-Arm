// @ts-check
import { defineConfig } from 'astro/config';

/**
 * 網頁原始碼放 site/src/，建置輸出到 _site/（見 CONVENTIONS.md §1）。
 * assets/ 留在 repo 根目錄不動，圖片透過 astro:assets 的 import.meta.glob 取用，
 * 由 Astro 自動產生 WebP 與多尺寸 —— 這樣 CONVENTIONS.md 的資產命名規則不用改。
 */
export default defineConfig({
  site: 'https://jason660519.github.io',
  base: '/Car-and-Robotic-Arm',
  srcDir: './site/src',
  publicDir: './site/public',
  outDir: './_site',
  build: { format: 'directory' },
  i18n: {
    defaultLocale: 'zh',
    locales: ['zh', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
