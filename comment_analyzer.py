import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CATEGORY_ALIAS_MAP = {
    "리밸런싱": "리밸런싱",
    "국내 주식 투자 비중": "리밸런싱",
    "국내주식": "리밸런싱",
    "자산배분": "리밸런싱",
    "연금개혁": "연금개혁",
    "구조개혁": "연금개혁",
    "모수개혁": "연금개혁",
    "연금제도": "연금개혁",
    "퇴직연금": "퇴직연금",
    "기금화": "퇴직연금",
    "기타": "기타",
}


def normalize_sentiment_label(sentiment: str | None) -> str:
    value = (sentiment or "").strip()
    if value == "광고":
        return "광고"
    if value == "긍정":
        return "긍정"
    if value == "부정":
        return "부정"
    if value == "중립":
        return "중립"
    if value == "오류":
        return "오류"
    if value == "기타":
        return "중립"
    return "중립"


def normalize_category_label(category: str | None) -> str:
    value = (category or "").strip()
    return CATEGORY_ALIAS_MAP.get(value, "기타")


def get_positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    try:
        value = int(raw_value)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        logger.warning("%s 값이 양의 정수가 아니어서 기본값 %s를 사용합니다: %s", name, default, raw_value)
        return default


def get_positive_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    try:
        value = float(raw_value)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        logger.warning("%s 값이 양의 숫자가 아니어서 기본값 %s를 사용합니다: %s", name, default, raw_value)
        return default


def normalize_analysis_item(item: dict | None) -> dict:
    if not isinstance(item, dict):
        return {
            "text": "",
            "sentiment": "오류",
            "category": "기타",
            "keyword": "응답형식오류",
        }

    return {
        "text": item.get("text", ""),
        "sentiment": normalize_sentiment_label(item.get("sentiment")),
        "category": normalize_category_label(item.get("category")),
        "keyword": item.get("keyword", "누락") or "누락",
    }


def _build_prompt(prompt_template: str, comments: list) -> str:
    strict_rules = """

[중요 제약]
- 입력 배열의 각 원소는 댓글 1개입니다.
- 출력 data 배열의 길이는 입력 댓글 수와 반드시 정확히 같아야 합니다.
- 입력 댓글 1개를 여러 행으로 쪼개지 마세요.
- 여러 댓글을 합치지 마세요.
- 출력 순서는 입력 순서와 반드시 같아야 합니다.
- text 값은 입력 댓글 원문과 동일한 댓글 1개를 그대로 유지하세요.
"""
    return f"{prompt_template}{strict_rules}\n\n댓글 목록: {json.dumps(comments, ensure_ascii=False)}"


def analyze_comments_with_llm(comments: list, prompt_template: str) -> list:
    """OpenRouter를 사용하여 댓글의 감성과 주요 키워드를 분석합니다."""
    if not comments:
        return []

    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        logger.error("openai 패키지가 설치되어 있지 않습니다.")
        return [
            {"text": t, "sentiment": "오류", "category": "기타", "keyword": "SDK누락"}
            for t in comments
        ]

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY가 설정되어 있지 않습니다. 로컬은 .env, GitHub Actions는 Secrets를 확인하세요.")
        return [
            {"text": t, "sentiment": "오류", "category": "기타", "keyword": "API키누락"}
            for t in comments
        ]

    # 1. OpenRouter가 권장하는 필수 헤더 추가
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:8501", 
            "X-Title": "NPS_PR_Dashboard"
        }
    )

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    batch_size = get_positive_int_env("OPENROUTER_BATCH_SIZE", 10)
    request_timeout = get_positive_float_env("OPENROUTER_TIMEOUT", 60.0)
    analyzed_data = []
    total_batches = (len(comments) + batch_size - 1) // batch_size

    for i in range(0, len(comments), batch_size):
        batch = comments[i:i + batch_size]
        batch_number = i // batch_size + 1
        logger.info("OpenRouter 배치 분석 시작: batch=%s/%s comments=%s model=%s", batch_number, total_batches, len(batch), model)

        prompt = _build_prompt(prompt_template, batch)
        content = ""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},  # JSON 구조 완벽 강제
                timeout=request_timeout,
            )

            content = response.choices[0].message.content.strip()
            result_dict = json.loads(content)  # 정규식 없이 깔끔하게 파싱!

            # 딕셔너리 안의 리스트를 추출
            if isinstance(result_dict, dict) and isinstance(result_dict.get("data"), list):
                if len(result_dict["data"]) != len(batch):
                    raise ValueError(
                        f"반환 개수 불일치: expected={len(batch)}, actual={len(result_dict['data'])}"
                    )
                analyzed_data.extend(normalize_analysis_item(item) for item in result_dict["data"])
            else:
                raise ValueError("JSON에 리스트 형태의 'data' 키가 없습니다.")

            logger.info("OpenRouter 배치 분석 완료: batch=%s/%s", batch_number, total_batches)

        except Exception as e:
            # 2. 대시보드에서 직접 에러 종류를 확인 가능하도록 추적 로직 강화
            error_type = type(e).__name__
            logger.warning("OpenRouter 배치 분석 실패 후 단건 재시도: batch=%s/%s error_type=%s error=%s", batch_number, total_batches, error_type, e)
            if content:
                logger.debug("OpenRouter 원본 응답 일부: %s", content[:500])

            # 배치 응답이 어긋나면 댓글 단위로 재시도해 순서를 강제합니다.
            for text in batch:
                single_prompt = _build_prompt(prompt_template, [text])
                single_content = ""
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": single_prompt}],
                        temperature=0.1,
                        response_format={"type": "json_object"},
                        timeout=request_timeout,
                    )
                    single_content = response.choices[0].message.content.strip()
                    result_dict = json.loads(single_content)
                    if not isinstance(result_dict, dict) or not isinstance(result_dict.get("data"), list) or len(result_dict["data"]) != 1:
                        raise ValueError("단건 재시도 결과 형식 오류")
                    analyzed_data.append(normalize_analysis_item(result_dict["data"][0]))
                except Exception as single_error:
                    single_error_type = type(single_error).__name__
                    logger.warning(
                        "OpenRouter 단건 재시도 실패: error_type=%s error=%s comment_preview=%s",
                        single_error_type,
                        single_error,
                        text[:80],
                    )
                    if single_content:
                        logger.debug("OpenRouter 단건 원본 응답 일부: %s", single_content[:500])
                    analyzed_data.append({
                        "text": text,
                        "sentiment": "오류",
                        "category": "기타",
                        "keyword": f"에러: {single_error_type}"
                    })

    return analyzed_data
