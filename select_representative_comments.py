"""분류별 대표 댓글(긍정/부정 각 5개)을 LLM으로 선별해 JSON으로 저장합니다."""

import argparse
import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from comment_analyzer import get_positive_float_env
from config_loader import (
    data_file_for_report,
    get_default_report,
    get_report_by_id,
    load_dashboard_config,
)

logger = logging.getLogger(__name__)

REPRESENTATIVE_DIR = Path("representative_comments")
TARGET_SENTIMENTS = ["긍정", "부정"]
CANDIDATE_POOL_SIZE = 60
SELECTION_COUNT = 10
PROMPT_TEXT_LIMIT = 300

SELECTION_PROMPT_TEMPLATE = """당신은 유튜브 댓글 여론 분석 전문가입니다.
아래는 "{category}" 분류로 분류된 {sentiment} 댓글 후보 목록입니다.
각 줄은 `번호. (추천 N) 댓글` 형식이며 추천수 내림차순으로 정렬되어 있습니다.

이 중에서 "{category}"에 대한 {sentiment} 여론을 대표하는 댓글을 최대 {count}개 고르세요.

[선정 기준]
1. 추천수가 많은 댓글을 우선합니다.
2. "{category}" 주제를 가장 잘 보여주는 댓글을 고릅니다.
3. 내용이 비슷한 댓글이 여러 개면 그중 하나만 고르고, 나머지 자리는 다른 관점의 댓글로 채워 다양한 의견이 드러나게 합니다.
4. 인신공격, 욕설, 근거 없는 단순 비방만 담긴 댓글은 제외합니다.
5. 기준을 충족하는 댓글이 {count}개 미만이면 충족하는 댓글만 고릅니다.

[후보]
{candidates}

반드시 아래 JSON 형식으로만 답하세요.
{{"selected": [선택한 후보 번호 목록]}}
"""


def representative_file_for_report(report: dict) -> str:
    return str(REPRESENTATIVE_DIR / f"representative_comments_{report['start_date']}.json")


def load_analyzed_rows(data_file: str) -> list[dict]:
    with open(data_file, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    parsed = []
    for row in rows:
        try:
            like_count = int(float(row.get("like_count") or 0))
        except (TypeError, ValueError):
            like_count = 0
        parsed.append(
            {
                "text": (row.get("text") or "").strip(),
                "sentiment": (row.get("sentiment") or "").strip(),
                "category": (row.get("category") or "").strip(),
                "like_count": like_count,
            }
        )
    return [row for row in parsed if row["text"]]


def build_candidates_block(candidates: list[dict]) -> str:
    lines = []
    for index, row in enumerate(candidates):
        text = row["text"].replace("\n", " ")
        if len(text) > PROMPT_TEXT_LIMIT:
            text = text[:PROMPT_TEXT_LIMIT] + "…"
        lines.append(f"{index}. (추천 {row['like_count']}) {text}")
    return "\n".join(lines)


def select_with_llm(client, model: str, category: str, sentiment: str, candidates: list[dict]) -> list[dict]:
    prompt = SELECTION_PROMPT_TEMPLATE.format(
        category=category,
        sentiment=sentiment,
        count=SELECTION_COUNT,
        candidates=build_candidates_block(candidates),
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
        timeout=get_positive_float_env("OPENROUTER_TIMEOUT", 60.0),
    )
    content = response.choices[0].message.content.strip()
    result = json.loads(content)
    selected_indices = result.get("selected") if isinstance(result, dict) else None
    if not isinstance(selected_indices, list):
        raise ValueError("JSON에 'selected' 리스트가 없습니다.")

    picked = []
    seen = set()
    for value in selected_indices:
        try:
            index = int(value)
        except (TypeError, ValueError):
            continue
        if 0 <= index < len(candidates) and index not in seen:
            picked.append(candidates[index])
            seen.add(index)
        if len(picked) >= SELECTION_COUNT:
            break
    return picked


def select_bucket(client, model: str, category: str, sentiment: str, rows: list[dict]) -> list[dict]:
    bucket_rows = [row for row in rows if row["category"] == category and row["sentiment"] == sentiment]
    if not bucket_rows:
        return []

    candidates = sorted(bucket_rows, key=lambda row: row["like_count"], reverse=True)[:CANDIDATE_POOL_SIZE]

    # 긍정 후보가 5개 이하면 그대로 사용하고, 부정은 비방 제외 판단을 위해 항상 LLM을 거칩니다.
    if sentiment == "긍정" and len(candidates) <= SELECTION_COUNT:
        return candidates

    if client is None:
        logger.warning("OPENROUTER_API_KEY가 없어 추천수 상위 댓글로 대체합니다: category=%s sentiment=%s", category, sentiment)
        return candidates[:SELECTION_COUNT]

    try:
        picked = select_with_llm(client, model, category, sentiment, candidates)
        logger.info("대표 댓글 선별 완료: category=%s sentiment=%s candidates=%s selected=%s", category, sentiment, len(candidates), len(picked))
        return picked
    except Exception:
        logger.exception("대표 댓글 LLM 선별 실패, 추천수 상위 댓글로 대체합니다: category=%s sentiment=%s", category, sentiment)
        return candidates[:SELECTION_COUNT]


def create_llm_client():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        logger.error("openai 패키지가 설치되어 있지 않습니다.")
        return None
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "NPS_PR_Dashboard",
        },
    )


def generate_for_report(report: dict, config: dict) -> dict:
    data_file = data_file_for_report(report)
    if not Path(data_file).exists():
        raise FileNotFoundError(f"댓글 파일을 찾지 못했습니다: {data_file}")

    rows = load_analyzed_rows(data_file)
    categories = sorted({row["category"] for row in rows if row["category"]})

    client = create_llm_client()
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    result = {
        "report_id": report.get("id"),
        "generated_at": datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S"),
        "categories": {},
    }
    for category in categories:
        buckets = {}
        for sentiment in TARGET_SENTIMENTS:
            selected = select_bucket(client, model, category, sentiment, rows)
            buckets[sentiment] = [
                {"text": row["text"], "like_count": row["like_count"]} for row in selected
            ]
        if any(buckets.values()):
            result["categories"][category] = buckets

    output_file = representative_file_for_report(report)
    REPRESENTATIVE_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
        file.write("\n")
    logger.info("대표 댓글 저장 완료: %s (categories=%s)", output_file, len(result["categories"]))
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    parser = argparse.ArgumentParser(description="분류별 대표 댓글을 선별합니다.")
    parser.add_argument("--report-id", help="dashboard_config.json의 report id (생략 시 기본 report)")
    args = parser.parse_args()

    config = load_dashboard_config()
    report = get_report_by_id(config, args.report_id) if args.report_id else get_default_report(config)
    if not report:
        raise ValueError("대상 report를 찾지 못했습니다.")
    generate_for_report(report, config)


if __name__ == "__main__":
    main()
