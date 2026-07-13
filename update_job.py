import logging
import os
import pandas as pd

from comment_collector import fetch_youtube_comments, fetch_video_stats
from comment_analyzer import (
    analyze_comments_with_llm,
    normalize_category_label,
    normalize_sentiment_label,
)
from config_loader import (
    get_collectable_reports,
    load_dashboard_config,
    resolve_prompt_file,
    data_file_for_report,
    stats_file_for_report,
)
from select_representative_comments import (
    generate_for_report as generate_representative_comments,
    representative_file_for_report,
)

COMMENT_COLUMNS = ["text", "sentiment", "category", "keyword", "like_count"]
logger = logging.getLogger(__name__)


def configure_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def normalize(text):
    return "".join(text.split()) if isinstance(text, str) else ""


def build_initial_stats_frame(report, title):
    columns = ["timestamp", "view_count", "like_count", "comment_count", "title"]
    start_at = report.get("video_start_at")
    if not start_at:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [
            {
                "timestamp": start_at,
                "view_count": 0,
                "like_count": 0,
                "comment_count": 0,
                "title": title,
            }
        ],
        columns=columns,
    )


def ensure_parent_directory(file_path):
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def load_existing_comments(data_file):
    if os.path.exists(data_file):
        existing_df = pd.read_csv(data_file)
    else:
        existing_df = pd.DataFrame(columns=COMMENT_COLUMNS)
        existing_df.to_csv(data_file, index=False)
        logger.info("댓글 CSV가 없어 새로 생성했습니다: %s", data_file)

    missing_columns = [column for column in COMMENT_COLUMNS if column not in existing_df.columns]
    if missing_columns:
        logger.warning("댓글 CSV에 누락 컬럼이 있어 기본값으로 보정합니다: file=%s columns=%s", data_file, missing_columns)
        for column in missing_columns:
            if column == "text":
                existing_df[column] = ""
            elif column == "like_count":
                existing_df[column] = 0
            else:
                existing_df[column] = "누락"

    existing_df["like_count"] = (
        pd.to_numeric(existing_df["like_count"], errors="coerce").fillna(0).astype(int)
    )
    return existing_df[COMMENT_COLUMNS]


def build_analyzed_rows(new_comments, analyzed_list, like_count_by_text):
    final_data = []
    for index, comment in enumerate(new_comments):
        result = analyzed_list[index] if index < len(analyzed_list) else {}
        if isinstance(result, dict) and result:
            item = result.copy()
        else:
            item = {"sentiment": "오류", "category": "기타", "keyword": "분석결과누락"}
        item["text"] = comment
        item["sentiment"] = normalize_sentiment_label(item.get("sentiment"))
        item["category"] = normalize_category_label(item.get("category"))
        item["keyword"] = item.get("keyword", "누락") or "누락"
        item["like_count"] = like_count_by_text.get(normalize(comment), 0)
        final_data.append(item)

    if len(analyzed_list) != len(new_comments):
        logger.warning("분석 결과 개수와 신규 댓글 수가 다릅니다: comments=%s results=%s", len(new_comments), len(analyzed_list))

    return final_data


def run_update_for_report(report, config):
    report_id = report.get("id", report.get("start_date"))
    video_url = report["video_url"]
    data_file = data_file_for_report(report)
    stats_file = stats_file_for_report(report)
    prompt_file = resolve_prompt_file(report, config)
    ensure_parent_directory(data_file)
    ensure_parent_directory(stats_file)

    logger.info("[%s] 업데이트 시작: data_file=%s stats_file=%s prompt_file=%s", report_id, data_file, stats_file, prompt_file)
    report_failed = False

    # 1. 영상 통계 업데이트
    try:
        stats = fetch_video_stats(video_url)
        if stats:
            if os.path.exists(stats_file):
                df_stats = pd.read_csv(stats_file)
            else:
                df_stats = build_initial_stats_frame(report, stats.get("title") or report.get("video_title", ""))

            stats_columns = ["timestamp", "view_count", "like_count", "comment_count", "title"]
            new_row = pd.DataFrame([{column: stats.get(column) for column in stats_columns}])
            df_stats = pd.concat([df_stats, new_row], ignore_index=True)
            df_stats.to_csv(stats_file, index=False)
            logger.info("[%s] 영상 통계 업데이트 완료: views=%s likes=%s comments=%s", report_id, stats["view_count"], stats["like_count"], stats["comment_count"])
        else:
            logger.warning("[%s] 영상 통계를 가져오지 못했습니다.", report_id)
            report_failed = True
    except Exception:
        logger.exception("[%s] 영상 통계 업데이트 중 오류가 발생했습니다. 댓글 수집은 계속 시도합니다.", report_id)
        report_failed = True

    # 2. 신규 댓글 수집 및 LLM 분석
    try:
        raw_comments = fetch_youtube_comments(video_url)
    except Exception:
        logger.exception("[%s] 댓글 수집 중 오류가 발생했습니다.", report_id)
        return False

    existing_df = load_existing_comments(data_file)

    like_count_by_text = {}
    for item in raw_comments:
        normalized_text = normalize(item["text"])
        if normalized_text:
            like_count_by_text[normalized_text] = max(
                like_count_by_text.get(normalized_text, 0), item["like_count"]
            )

    existing_normalized = set(normalize(text) for text in existing_df["text"].tolist()) if not existing_df.empty else set()

    # 기존 댓글의 추천수를 이번 수집 값으로 갱신합니다.
    likes_changed = False
    if not existing_df.empty:
        refreshed_likes = existing_df.apply(
            lambda row: like_count_by_text.get(normalize(row["text"]), row["like_count"]),
            axis=1,
        ).astype(int)
        likes_changed = not refreshed_likes.equals(existing_df["like_count"])
        existing_df["like_count"] = refreshed_likes

    # 중복되지 않은 신규 댓글만 선별 (공백 무시 기준)
    new_comments = []
    seen_in_batch = set()
    for item in raw_comments:
        normalized_comment = normalize(item["text"])
        if normalized_comment not in existing_normalized and normalized_comment not in seen_in_batch:
            new_comments.append(item["text"])
            seen_in_batch.add(normalized_comment)

    logger.info("[%s] 댓글 비교 완료: fetched=%s existing=%s new=%s", report_id, len(raw_comments), len(existing_normalized), len(new_comments))

    if new_comments and os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as file:
            prompt_template = file.read()

        analyzed_list = analyze_comments_with_llm(new_comments, prompt_template)
        if analyzed_list:
            # LLM이 반환한 text가 변형되었을 수 있으므로 원본 댓글을 기준으로 저장합니다.
            final_data = build_analyzed_rows(new_comments, analyzed_list, like_count_by_text)
            new_df = pd.DataFrame(final_data)
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            updated_df.to_csv(data_file, index=False)
            logger.info("[%s] 새 댓글 %s개 분석 및 저장 완료.", report_id, len(new_comments))
        else:
            logger.error("[%s] 신규 댓글이 있었지만 분석 결과가 비어 있습니다.", report_id)
            return False
    elif new_comments:
        logger.error("[%s] 프롬프트 파일이 없어 새 댓글 분석을 건너뜁니다: %s", report_id, prompt_file)
        return False
    else:
        if likes_changed:
            existing_df.to_csv(data_file, index=False)
            logger.info("[%s] 기존 댓글 추천수를 갱신했습니다.", report_id)
        logger.info("[%s] 분석할 새로운 댓글이 없습니다.", report_id)

    # 3. 분류별 대표 댓글 갱신 (새 댓글이 있거나 결과 파일이 없을 때만 LLM 호출)
    try:
        if new_comments or not os.path.exists(representative_file_for_report(report)):
            generate_representative_comments(report, config)
    except Exception:
        logger.exception("[%s] 대표 댓글 선별 중 오류가 발생했습니다.", report_id)

    return not report_failed


def main():
    configure_logging()
    dashboard_config = load_dashboard_config()
    reports = get_collectable_reports(dashboard_config)
    target_report_id = os.getenv("REPORT_ID", "").strip()
    if target_report_id:
        reports = [report for report in reports if report.get("id") == target_report_id]
        if not reports:
            raise SystemExit(f"요청한 report를 찾을 수 없습니다: {target_report_id}")
    if not reports:
        logger.warning("수집 대상 영상이 없습니다. dashboard_config.json의 reports 설정을 확인하세요.")
        return

    failed_reports = []
    for report_item in reports:
        try:
            if not run_update_for_report(report_item, dashboard_config):
                failed_reports.append(report_item.get("id", report_item.get("start_date", "unknown")))
        except Exception:
            report_id = report_item.get("id", report_item.get("start_date", "unknown"))
            failed_reports.append(report_id)
            logger.exception("[%s] 처리 중 예상하지 못한 오류가 발생했습니다.", report_id)

    logger.info("업데이트 요약: total=%s success=%s failed=%s", len(reports), len(reports) - len(failed_reports), len(failed_reports))
    if failed_reports:
        raise SystemExit(f"실패한 report가 있습니다: {', '.join(failed_reports)}")


if __name__ == "__main__":
    main()
