import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from comment_collector import fetch_video_stats
from config_loader import CONFIG_FILE, load_dashboard_config


VIDEO_ID_PATTERN = re.compile(r"^[0-9A-Za-z_-]{11}$")
URL_PATTERN = re.compile(r"https?://[^\s<>()]+")
SUPPORTED_HOSTS = {"youtube.com", "m.youtube.com", "youtu.be"}


def extract_request_url(value: str) -> str:
    match = URL_PATTERN.search(value or "")
    if not match:
        raise ValueError("요청에서 유튜브 URL을 찾지 못했습니다.")
    return match.group(0).rstrip(".,)")


def normalize_youtube_url(value: str) -> tuple[str, str]:
    parsed = urlparse(extract_request_url(value))
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if host not in SUPPORTED_HOSTS:
        raise ValueError("youtube.com 또는 youtu.be 영상 주소만 사용할 수 있습니다.")

    if host == "youtu.be":
        video_id = next((part for part in parsed.path.split("/") if part), "")
    else:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if not video_id:
            parts = [part for part in parsed.path.split("/") if part]
            video_id = parts[1] if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"} else ""

    if not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise ValueError("유효한 유튜브 영상 ID를 찾지 못했습니다.")

    return f"https://www.youtube.com/watch?v={video_id}", video_id


def build_report(config: dict, youtube_url: str, video_id: str) -> tuple[dict, bool]:
    for report in config.get("reports", []):
        try:
            _, existing_video_id = normalize_youtube_url(report.get("video_url", ""))
        except ValueError:
            continue
        if existing_video_id == video_id:
            # 비활성화된 리포트를 다시 요청하면 재활성화하고 기본 화면으로 되돌립니다.
            changed = False
            if not report.get("enabled", True):
                report["enabled"] = True
                changed = True
            if not report.get("collect_enabled", True):
                report["collect_enabled"] = True
                changed = True
            if config.get("default_report_id") != report["id"]:
                config["default_report_id"] = report["id"]
                changed = True
            return report, changed

    stats = fetch_video_stats(youtube_url)
    if not stats:
        raise ValueError("유튜브에서 영상 정보를 불러오지 못했습니다.")

    now = datetime.now(ZoneInfo("Asia/Seoul"))
    title = stats.get("title") or "새 유튜브 영상"
    published_at = stats.get("published_at") or ""
    try:
        published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00")).astimezone(
            ZoneInfo("Asia/Seoul")
        ).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        published_at = ""
    report = {
        "id": f"youtube_{video_id}",
        "tab_label": title[:32],
        "video_title": title,
        "video_url": youtube_url,
        "start_date": now.strftime("%Y%m%d_%H%M%S"),
        "video_start_at": published_at,
        "prompt_file": config.get("default_prompt_file", "prompt/prompt_base.txt"),
        "enabled": True,
        "collect_enabled": True,
    }
    config.setdefault("reports", []).append(report)
    config["default_report_id"] = report["id"]
    return report, True


def main() -> None:
    request_text = " ".join(sys.argv[1:]).strip() or os.getenv("YOUTUBE_URL", "")
    youtube_url, video_id = normalize_youtube_url(request_text)
    config = load_dashboard_config()
    report, created = build_report(config, youtube_url, video_id)

    if created:
        Path(CONFIG_FILE).write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps({"report_id": report["id"], "created": created}, ensure_ascii=False))


if __name__ == "__main__":
    main()
