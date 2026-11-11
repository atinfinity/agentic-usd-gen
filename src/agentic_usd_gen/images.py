"""商品画像のダウンロード。

取得したファイルは信頼できないデータとして扱い、Pillow で画像として読めたものだけを
PNG に再エンコードして保存する。
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from PIL import Image

from .spec import ProductSpec

log = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) agentic-usd-gen/0.1"
MAX_BYTES = 20 * 1024 * 1024
MIN_SIDE = 200
MAX_PAGE_IMAGES = 4

_OG_IMAGE = re.compile(
    r"<meta[^>]+(?:property|name)=[\"'](?:og:image|twitter:image)[\"'][^>]+content=[\"']([^\"']+)", re.I
)


def _get(url: str, **kw) -> requests.Response:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20, stream=True, **kw)
    r.raise_for_status()
    return r


def _fetch_image(url: str) -> Image.Image | None:
    try:
        r = _get(url)
        data = r.raw.read(MAX_BYTES + 1, decode_content=True)
        if len(data) > MAX_BYTES:
            log.warning("大きすぎるため除外: %s", url)
            return None
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:  # noqa: BLE001 - 取得失敗は候補を捨てるだけ
        log.info("画像取得に失敗: %s (%s)", url, e)
        return None
    if min(img.size) < MIN_SIDE:
        log.info("小さすぎるため除外: %s %s", url, img.size)
        return None
    if img.mode in ("RGBA", "LA", "P"):
        # 透過 PNG は白背景に合成する（輪郭抽出が白背景を前提にしているため）
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
    return img.convert("RGB")


def _page_image_urls(page_url: str) -> list[str]:
    """商品ページから og:image を拾う（Claude が画像 URL を返せなかったときの予備）。"""
    try:
        html = _get(page_url).raw.read(2 * 1024 * 1024, decode_content=True).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        log.info("ページ取得に失敗: %s (%s)", page_url, e)
        return []
    return [urljoin(page_url, u) for u in _OG_IMAGE.findall(html)][:MAX_PAGE_IMAGES]


def download_images(spec: ProductSpec, dest: Path, limit: int = 8) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    urls = [c.url for c in spec.image_candidates]
    pages = [c.source_page for c in spec.image_candidates if c.source_page] + [s.url for s in spec.sources]

    saved: list[Path] = []
    manifest: list[str] = []
    seen: set[str] = set()

    def try_url(url: str) -> None:
        if url in seen or len(saved) >= limit:
            return
        seen.add(url)
        img = _fetch_image(url)
        if img is None:
            return
        path = dest / f"{len(saved):02d}.png"
        img.save(path)
        saved.append(path)
        manifest.append(f"{path.name}\t{url}")

    for u in urls:
        try_url(u)
    if len(saved) < 2:
        for page in dict.fromkeys(pages):
            for u in _page_image_urls(page):
                try_url(u)
    (dest / "sources.tsv").write_text("\n".join(manifest) + "\n")
    return saved
