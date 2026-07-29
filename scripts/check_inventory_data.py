#!/usr/bin/env python3
"""驗證 site/data/modules.js 的完整性。

抽出資料後檢查：圖片檔案存在、id 不重複、中英文欄位齊全、
圖片路徑符合 CONVENTIONS.md §3.3 的 NNN_ 命名。

    uv run python scripts/check_inventory_data.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "site" / "data" / "modules.js"
LANGS = ("zh", "en")
# 必填。arduinoWiring / stm32Wiring 刻意不列入 —— 樹莓派專用模組
# （M.2 HAT、USB 相機）本來就沒有 Arduino / STM32 接線，空陣列是正確資料。
I18N_FIELDS = ("title", "desc", "specs", "codeSnippet")
ASSET_NAME = re.compile(r"^\d{3}_[A-Za-z0-9_]+\.(jpg|png)$")


def load_modules() -> list[dict]:
    """用 node 求值資料檔，回傳模組陣列。

    modules.js 是給瀏覽器用的 classic script，`const MODULES` 不會掛到 module.exports，
    所以不能用 require()，要在 vm context 裡跑完再取完成值。
    """
    script = f"""
        const fs = require('fs'), vm = require('vm');
        const src = fs.readFileSync({json.dumps(str(DATA))}, 'utf8');
        process.stdout.write(vm.runInNewContext(src + '\\nJSON.stringify(MODULES)'));
    """
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, cwd=REPO, check=False
    )
    if result.returncode != 0:
        sys.exit(f"無法載入 {DATA.relative_to(REPO)}：\n{result.stderr}")
    return json.loads(result.stdout)


def main() -> int:
    modules = load_modules()
    problems: list[str] = []

    seen_ids: set[str] = set()
    for m in modules:
        mid = m.get("id", "<無 id>")
        if mid in seen_ids:
            problems.append(f"{mid}: id 重複")
        seen_ids.add(mid)

        for key in ("number", "name", "category", "tags", "images"):
            if not m.get(key):
                problems.append(f"{mid}: 缺少語言無關欄位 {key}")

        for lang in LANGS:
            block = m.get("i18n", {}).get(lang)
            if not block:
                problems.append(f"{mid}: 缺少 {lang} 語言區塊")
                continue
            for field in I18N_FIELDS:
                if not block.get(field):
                    problems.append(f"{mid}: {lang}.{field} 是空的")

        for rel in m.get("images", []):
            path = REPO / rel
            if not path.exists():
                problems.append(f"{mid}: 圖片不存在 {rel}")
            elif not ASSET_NAME.match(path.name):
                problems.append(f"{mid}: 檔名不符 CONVENTIONS.md §3.3 — {path.name}")

    # 反向檢查：assets/inventory/ 裡有哪些照片還沒被任何模組收錄
    used = {REPO / p for m in modules for p in m.get("images", [])}
    orphans = sorted(
        p.name
        for p in (REPO / "assets" / "inventory").iterdir()
        if p.suffix.lower() in (".jpg", ".png") and p not in used
    )

    print(f"模組 {len(modules)} 個，引用圖片 {len(used)} 張")
    if orphans:
        print(f"\n未被收錄的照片 {len(orphans)} 張（不是錯誤，但值得補進去）：")
        for name in orphans:
            print(f"  · {name}")

    if problems:
        print(f"\n✗ {len(problems)} 個問題：")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\n✓ 資料完整")
    return 0


if __name__ == "__main__":
    sys.exit(main())
