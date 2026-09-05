# scripts/check_stc_brand_pack.py
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from xpand_stc_brand_kit import BrandKit  # noqa: E402


def main() -> int:
    pack_path = ROOT / "brand_assets" / "stc_bank" / "stc_bank_brand_pack.json"
    if not pack_path.exists():
        print("❌ Missing brand pack:", pack_path)
        return 1

    pack = BrandKit.load(pack_path)
    print("==========================================")
    print(" STC BRAND PACK AUDIT")
    print("==========================================")
    print(f"brand = {pack.brand_name}")
    print(f"total_assets = {len(pack.assets)}")

    missing = []
    for asset in pack.assets:
        asset_path = pack.resolve_asset_path(asset.path)
        if asset_path.exists():
            print(f"✅ {asset.asset_id} -> {asset_path}")
        else:
            print(f"❌ {asset.asset_id} -> {asset_path}")
            missing.append(asset.asset_id)

    print("------------------------------------------")
    if missing:
        print("❌ Missing assets:")
        for item in missing:
            print(" -", item)
        return 1

    print("✅ All STC brand assets exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
