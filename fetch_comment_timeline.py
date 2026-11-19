"""댓글 작성 시각 타임라인을 저장합니다 (LLM 사용 없음, YouTube API만).

게재 후 한참 뒤에 등록해 조회수 기록이 없는 영상용입니다. 대시보드는 report의
`comment_timeline_file`이 있으면 상세 탭에서 조회수 대신 누적 댓글 수 추이를 그립니다.
"""

import argparse
import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from comment_collector import extract_video_id, get_json
from config_loader import get_report_by_id, load_dashboard_config

TIMELINE_DIR = Path("comment_timeline")
KST = ZoneInfo("Asia/Seoul")


def fetch_comment_times(video_url: str) -> list[dict]:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY가 설정되어 있지 않습니다.")
    rows, token = [], None
    while True:
        params = {"part": "snippet", "videoId": extract_video_id(video_url), "maxResults": 100, "key": api_key}
        if token:
            params["pageToken"] = token
        response = get_json("commentThreads", params)
        for item in response.get("items", []):
            published = item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
            kst = datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(KST)
            rows.append({
                "published_at": kst.strftime("%Y-%m-%d %H:%M:%S"),
                "reply_count": int(item["snippet"].get("totalReplyCount", 0) or 0),
            })
        token = response.get("nextPageToken")
        if not token:
            break
    rows.sort(key=lambda row: row["published_at"])
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="댓글 작성 시각 타임라인을 저장합니다.")
    parser.add_argument("--report-id", required=True)
    args = parser.parse_args()

    report = get_report_by_id(load_dashboard_config(), args.report_id)
    if not report:
        raise ValueError(f"report를 찾지 못했습니다: {args.report_id}")
    rows = fetch_comment_times(report["video_url"])
    TIMELINE_DIR.mkdir(exist_ok=True)
    output = TIMELINE_DIR / f"comment_timeline_{report['start_date']}.csv"
    with open(output, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["published_at", "reply_count"])
        writer.writeheader()
        writer.writerows(rows)
    logging.info("저장 완료: %s (%s건)", output, len(rows))


if __name__ == "__main__":
    main()
