import os
import re
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

logger = logging.getLogger(__name__)
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"


def get_request_timeout() -> float:
    try:
        return float(os.getenv("YOUTUBE_API_TIMEOUT", "30"))
    except ValueError:
        logger.warning("YOUTUBE_API_TIMEOUT 값이 숫자가 아니어서 기본값 30초를 사용합니다.")
        return 30.0


def redacted_params(params: dict) -> dict:
    safe_params = params.copy()
    if "key" in safe_params:
        safe_params["key"] = "***"
    return safe_params


def get_json(endpoint: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    full_url = f"{YOUTUBE_API_BASE_URL}/{endpoint}?{query}"
    timeout = get_request_timeout()

    logger.debug("YouTube API 요청: endpoint=%s params=%s", endpoint, redacted_params(params))
    try:
        with urllib.request.urlopen(full_url, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(
            f"YouTube API 요청 실패: endpoint={endpoint}, status={error.code}, body={body}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"YouTube API 연결 실패: endpoint={endpoint}, reason={error.reason}"
        ) from error


def extract_video_id(url: str) -> str:
    """유튜브 URL에서 video_id를 추출합니다."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url  # 이미 ID 형태인 경우


def fetch_youtube_comments(video_url: str, max_results: int = None) -> list:
    """유튜브 영상의 댓글을 수집합니다. max_results가 없으면 모든 댓글을 수집합니다."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY가 설정되어 있지 않습니다. 로컬은 .env, GitHub Actions는 Secrets를 확인하세요.")

    video_id = extract_video_id(video_url)

    comments = []
    next_page_token = None
    page_count = 0

    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,  # 한 페이지당 최대 100개씩 호출
            "textFormat": "plainText",
            "key": api_key,
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        response = get_json("commentThreads", params)
        page_count += 1

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)

        logger.debug("댓글 페이지 수집 완료: video_id=%s page=%s total=%s", video_id, page_count, len(comments))

        next_page_token = response.get("nextPageToken")

        # 다음 페이지가 없으면(댓글을 끝까지 다 가져왔으면) 루프 종료
        if not next_page_token:
            break

        # 만약 최대 개수 제한이 설정되어 있고, 그 수를 넘었다면 종료
        if max_results and len(comments) >= max_results:
            comments = comments[:max_results]
            break

    logger.info("댓글 수집 완료: video_id=%s comments=%s pages=%s", video_id, len(comments), page_count)
    return comments


def fetch_video_stats(video_url: str) -> dict:
    """영상의 현재 조회수, 좋아요 수 등 통계를 가져옵니다."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY가 설정되어 있지 않습니다. 로컬은 .env, GitHub Actions는 Secrets를 확인하세요.")

    video_id = extract_video_id(video_url)

    response = get_json("videos", {"part": "statistics,snippet", "id": video_id, "key": api_key})

    if not response.get("items"):
        logger.warning("영상 통계 응답에 items가 없습니다: video_id=%s", video_id)
        return None

    item = response["items"][0]
    stats = item["statistics"]
    kst_now = datetime.now(ZoneInfo("Asia/Seoul"))

    return {
        "title": item["snippet"]["title"],
        "published_at": item["snippet"].get("publishedAt"),
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
        "comment_count": int(stats.get("commentCount", 0)),
        "timestamp": kst_now.strftime("%Y-%m-%d %H:%M:%S")
    }
