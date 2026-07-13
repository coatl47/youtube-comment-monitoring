import argparse
import csv
from collections import Counter
from pathlib import Path

from comment_analyzer import (
    analyze_comments_with_llm,
    normalize_category_label,
    normalize_sentiment_label,
)
from config_loader import (
    data_file_for_report,
    get_default_report,
    get_report_by_id,
    load_dashboard_config,
    resolve_prompt_file,
)
from select_representative_comments import generate_for_report as generate_representative_comments


def parse_like_count(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="기존 댓글 CSV를 다시 분석합니다.")
    parser.add_argument("--report-id", help="dashboard_config.json의 report id")
    parser.add_argument("--all", action="store_true", help="활성화된 모든 report를 처리합니다.")
    parser.add_argument(
        "--normalize-only",
        action="store_true",
        help="LLM 재호출 없이 기존 category 값을 공통 체계로 정규화합니다.",
    )
    return parser.parse_args()

def write_rows(data_file: str, rows: list[dict]) -> None:
    with open(data_file, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "sentiment", "category", "keyword", "like_count"])
        writer.writeheader()
        writer.writerows(rows)


def normalize_existing_rows(data_file: str) -> list[dict]:
    with open(data_file, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    normalized_rows = []
    for row in rows:
        normalized_rows.append(
            {
                "text": row.get("text", ""),
                "sentiment": normalize_sentiment_label(row.get("sentiment")),
                "category": normalize_category_label(row.get("category")),
                "keyword": row.get("keyword", "누락") or "누락",
                "like_count": parse_like_count(row.get("like_count")),
            }
        )

    write_rows(data_file, normalized_rows)
    return normalized_rows


def analyze_report(report: dict, config: dict, normalize_only: bool = False) -> None:
    data_file = data_file_for_report(report)
    if not Path(data_file).exists():
        raise FileNotFoundError(f"댓글 파일을 찾지 못했습니다: {data_file}")

    if normalize_only:
        final_rows = normalize_existing_rows(data_file)
        print(f"normalized {len(final_rows)} comments in {data_file} ({report.get('id')})")
        print("sentiment:", Counter(row["sentiment"] for row in final_rows))
        print("category:", Counter(row["category"] for row in final_rows))
        return

    prompt_file = resolve_prompt_file(report, config)

    with open(prompt_file, "r", encoding="utf-8") as file:
        prompt_template = file.read()

    with open(data_file, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    source_rows = [row for row in rows if row.get("text")]
    comments = [row["text"] for row in source_rows]
    analyzed_rows = analyze_comments_with_llm(comments, prompt_template)

    final_rows = []
    for index, source_row in enumerate(source_rows):
        analyzed = analyzed_rows[index] if index < len(analyzed_rows) else {}
        final_rows.append(
            {
                "text": source_row["text"],
                "sentiment": normalize_sentiment_label(analyzed.get("sentiment", "오류")),
                "category": normalize_category_label(analyzed.get("category", "기타")),
                "keyword": analyzed.get("keyword", "누락"),
                "like_count": parse_like_count(source_row.get("like_count")),
            }
        )

    write_rows(data_file, final_rows)

    print(f"re-analyzed {len(final_rows)} comments in {data_file} ({report.get('id')})")
    print("sentiment:", Counter(row["sentiment"] for row in final_rows))
    print("category:", Counter(row["category"] for row in final_rows))

    generate_representative_comments(report, config)


def main() -> None:
    args = parse_args()
    config = load_dashboard_config()

    if args.all:
        reports = [report for report in config.get("reports", []) if report.get("enabled", True)]
    else:
        report = get_report_by_id(config, args.report_id) if args.report_id else get_default_report(config)
        if not report:
            raise ValueError("재분석할 report를 찾지 못했습니다.")
        reports = [report]

    for report in reports:
        analyze_report(report, config, normalize_only=args.normalize_only)


if __name__ == "__main__":
    main()
