import type { ImageMetadata } from 'astro';

/**
 * 把資料檔裡的資產路徑（相對 repo 根目錄，如 `assets/inventory/001_x.jpg`）
 * 換成 Astro 的 ImageMetadata，交給 <Image> 產生 WebP 與多尺寸。
 *
 * assets/ 不在 srcDir 底下，所以用 Vite 的 root-relative glob 撈進來。
 */
const files = import.meta.glob<{ default: ImageMetadata }>(
  '/assets/**/*.{jpg,jpeg,png,JPG,PNG}',
  { eager: true },
);

export function asset(path: string): ImageMetadata {
  const key = '/' + path.replace(/^\/+/, '');
  const hit = files[key];
  if (!hit) {
    throw new Error(
      `找不到資產 ${key}。資料檔裡的路徑要相對 repo 根目錄，見 CONVENTIONS.md §4.5`,
    );
  }
  return hit.default;
}

export function hasAsset(path: string): boolean {
  return ('/' + path.replace(/^\/+/, '')) in files;
}
