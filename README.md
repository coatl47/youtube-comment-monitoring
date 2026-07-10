# 국민연금 이사장 유튜브 여론 모니터링 대시보드

[실시간 대시보드 바로가기](https://roy8in.github.io/youtube-comment-monitoring/)

이 저장소는 여러 개의 유튜브 영상 댓글을 자동으로 수집하고, 새로 발견된 댓글만 AI로 분석한 뒤, 그 결과를 웹 대시보드로 보여주는 프로젝트입니다.

처음 이 프로젝트를 맡는 분이 이해해야 할 핵심은 세 가지입니다.

1. **GitHub 저장소**가 코드와 데이터 파일을 보관합니다.
2. **GitHub Actions**가 정해진 시간마다 Python 스크립트를 실행해 데이터를 갱신합니다.
3. **OpenRouter**가 댓글을 읽고 감성, 주제, 키워드를 분석하는 AI 모델 호출 통로 역할을 합니다.

이 README는 GitHub나 OpenRouter에 익숙하지 않은 분도 전체 흐름을 따라갈 수 있도록, 개념 설명부터 실제 수정 방법까지 자세히 정리한 문서입니다.

## 현재 프로젝트가 하는 일

이 프로젝트는 특정 유튜브 영상들에 달린 댓글을 모니터링합니다. 각 영상에 대해 아래 정보를 저장합니다.

- 영상 조회수, 좋아요 수, 댓글 수의 시간별 변화
- 댓글 원문
- 댓글의 감성 분류: `긍정`, `중립`, `부정`, `광고`, `오류`
- 댓글의 주제 분류: 예를 들어 `운용성과`, `투자전략`, `연금제도`, `정부개입·거버넌스` 등
- 댓글에서 뽑은 주요 키워드

대시보드는 이 데이터를 바탕으로 아래 화면을 보여줍니다.

- 전체 영상의 종합 현황
- 영상별 탭
- 조회수 추이
- 감성 분포
- 주제별 여론 분포
- 분석된 댓글 목록

즉, 이 저장소는 단순한 HTML 페이지가 아니라 **데이터 수집, AI 분석, 결과 저장, 웹 시각화가 한 번에 묶인 자동화 시스템**입니다.

## 전체 작동 흐름 한눈에 보기

```text
dashboard_config.json
        |
        v
update_job.py
        |
        +--> YouTube Data API에서 영상 통계와 댓글 수집
        |
        +--> 기존 CSV와 비교해 새 댓글만 선별
        |
        +--> OpenRouter로 새 댓글 감성/주제/키워드 분석
        |
        +--> analyzed_comments/ 와 video_stats/ CSV 파일 갱신
        |
        v
GitHub Actions가 변경된 CSV를 commit 후 push
        |
        v
GitHub Pages가 index.html 대시보드를 공개
        |
        v
브라우저가 dashboard_config.json과 CSV 파일을 읽어 차트 표시
```

조금 더 풀어서 말하면 다음 순서입니다.

1. `dashboard_config.json`에 모니터링할 유튜브 영상 목록이 적혀 있습니다.
2. GitHub Actions가 일정 시간마다 `update_job.py`를 실행합니다.
3. `update_job.py`는 각 영상의 최신 통계와 댓글을 YouTube API로 가져옵니다.
4. 이미 CSV에 저장된 댓글은 다시 분석하지 않고, 새 댓글만 골라냅니다.
5. 새 댓글이 있으면 OpenRouter를 통해 AI 모델에 분석을 요청합니다.
6. 분석 결과는 `analyzed_comments/` 폴더의 CSV에 저장됩니다.
7. 영상 통계는 `video_stats/` 폴더의 CSV에 저장됩니다.
8. 저장된 CSV가 GitHub에 자동 커밋됩니다.
9. `index.html`은 GitHub Pages에서 공개되고, CSV를 읽어 차트를 그립니다.

## GitHub가 무엇인가요?

GitHub는 코드와 파일을 인터넷에 보관하고, 여러 사람이 함께 관리할 수 있게 해주는 서비스입니다.

이 프로젝트에서 GitHub는 아래 역할을 합니다.

- 프로젝트 파일을 보관하는 장소
- 누가 언제 어떤 파일을 바꾸었는지 기록하는 장소
- 웹 대시보드를 공개하는 장소
- 정해진 시간마다 자동 업데이트 작업을 실행하는 장소

GitHub를 이해할 때 자주 나오는 단어는 다음과 같습니다.

### Git

Git은 파일 변경 이력을 관리하는 도구입니다.

예를 들어 README를 수정하거나 CSV 파일이 갱신되면 Git은 “어떤 파일의 어떤 줄이 바뀌었는지”를 기록할 수 있습니다.

### GitHub

GitHub는 Git으로 관리되는 프로젝트를 인터넷에 올려두는 서비스입니다.

이 프로젝트의 GitHub 주소는 아래와 같습니다.

```text
https://github.com/roy8in/youtube-comment-monitoring
```

### Repository 또는 저장소

Repository는 프로젝트 폴더 전체를 뜻합니다.

이 저장소 안에는 Python 코드, HTML 대시보드, CSV 데이터, 프롬프트, GitHub Actions 설정 파일이 함께 들어 있습니다.

### Commit

Commit은 파일 변경사항을 하나의 기록으로 저장하는 것입니다.

예를 들어 자동 업데이트가 새 댓글 분석 결과를 CSV에 저장하면, GitHub Actions가 다음과 같은 커밋을 만들 수 있습니다.

```text
Auto-update data
```

이 커밋은 “이 시점에 데이터가 갱신되었다”는 기록입니다.

### Push

Push는 내 컴퓨터 또는 GitHub Actions에서 만든 커밋을 GitHub 서버로 올리는 작업입니다.

이 프로젝트에서는 GitHub Actions가 CSV를 갱신한 뒤 자동으로 push합니다.

### Pull

Pull은 GitHub에 올라간 최신 변경사항을 내 로컬 컴퓨터로 가져오는 작업입니다.

로컬에서 작업하기 전에는 보통 아래 명령으로 최신 상태를 가져옵니다.

```bash
git pull --ff-only origin main
```

### Branch

Branch는 작업 흐름을 나누는 가지입니다.

이 프로젝트는 기본적으로 `main` 브랜치를 사용합니다. GitHub Pages와 자동 업데이트도 `main`을 기준으로 동작합니다.

### GitHub Actions

GitHub Actions는 GitHub 안에서 자동으로 명령을 실행해 주는 기능입니다.

이 프로젝트에서는 `.github/workflows/update_data.yml` 파일이 GitHub Actions 설정입니다. 이 파일은 “언제, 어떤 환경에서, 어떤 명령을 실행할지”를 정의합니다.

### GitHub Pages

GitHub Pages는 GitHub 저장소 안의 HTML 파일을 웹사이트처럼 공개해 주는 기능입니다.

이 프로젝트에서는 `index.html`이 대시보드 화면이고, GitHub Pages가 그 파일을 웹에서 볼 수 있게 해줍니다.

### GitHub Secrets

Secrets는 API 키처럼 외부에 공개되면 안 되는 값을 GitHub에 안전하게 저장하는 기능입니다.

이 프로젝트는 아래 secret이 필요합니다.

- `YOUTUBE_API_KEY`
- `OPENROUTER_API_KEY`

이 값들은 코드에 직접 쓰면 안 됩니다. GitHub Actions가 실행될 때 환경 변수로만 전달되게 해야 합니다.

## API가 무엇인가요?

API는 **Application Programming Interface**의 줄임말입니다.

처음 들으면 어렵게 느껴질 수 있지만, 아주 쉽게 말하면 **프로그램끼리 서로 요청하고 답을 받기 위한 약속된 창구**입니다.

사람은 유튜브 웹사이트에 들어가서 영상을 보고 댓글을 읽을 수 있습니다. 하지만 Python 프로그램은 사람처럼 브라우저 화면을 눈으로 보고 클릭하지 않습니다. 대신 YouTube가 정해 둔 API 주소로 요청을 보냅니다.

예를 들어 이 프로젝트의 Python 코드는 YouTube에 대략 이런 요청을 보냅니다.

```text
이 영상의 댓글 목록을 주세요.
이 영상의 현재 조회수, 좋아요 수, 댓글 수를 주세요.
```

그러면 YouTube API는 사람이 읽는 웹페이지가 아니라, 프로그램이 다루기 쉬운 JSON 형식의 데이터를 돌려줍니다.

OpenRouter API도 비슷합니다. 이 프로젝트는 OpenRouter에 대략 이런 요청을 보냅니다.

```text
아래 댓글들을 읽고 감성, 주제, 키워드를 JSON으로 분류해 주세요.
```

그러면 OpenRouter는 AI 모델의 분석 결과를 JSON으로 돌려줍니다.

즉, 이 프로젝트에서 API는 두 곳에서 핵심 역할을 합니다.

- **YouTube Data API**: 유튜브 영상 통계와 댓글을 가져오는 창구
- **OpenRouter API**: 댓글을 AI 모델로 분석하는 창구

### API Key는 무엇인가요?

API Key는 API를 사용할 때 필요한 비밀번호나 출입증 같은 값입니다.

서비스 제공자는 API Key를 보고 아래를 판단합니다.

- 누가 요청했는지
- 이 요청이 허용된 요청인지
- 사용량이 얼마나 되는지
- 비용이나 제한을 어떻게 적용할지

그래서 API Key는 절대 공개하면 안 됩니다. GitHub 공개 저장소에 API Key를 직접 적어 두면 다른 사람이 그 키를 가져가서 사용할 수 있습니다.

이 프로젝트에서는 API Key를 두 방식으로 관리합니다.

- 로컬 실행: `.env` 파일에 저장
- GitHub Actions 실행: GitHub Secrets에 저장

### API 호출은 비용이나 제한이 있을 수 있습니다

API는 무료로 무제한 사용할 수 있는 경우가 많지 않습니다.

YouTube Data API는 할당량 제한이 있고, OpenRouter는 사용하는 모델과 사용량에 따라 비용이 발생할 수 있습니다.

이 프로젝트가 새 댓글만 분석하도록 만든 이유도 여기에 있습니다. 이미 분석한 댓글을 매번 다시 OpenRouter에 보내면 비용과 시간이 불필요하게 늘어납니다.

### 이 프로젝트에서 API 흐름을 다시 보면

```text
Python 코드
   |
   +--> YouTube Data API
   |       |
   |       +--> 영상 통계와 댓글 반환
   |
   +--> OpenRouter API
           |
           +--> 댓글 분석 결과 반환
```

이 흐름 덕분에 사람이 매번 유튜브에 들어가 댓글을 복사하고, AI에게 붙여 넣고, 다시 표로 정리하는 일을 자동화할 수 있습니다.

## OpenRouter가 무엇인가요?

OpenRouter는 여러 AI 모델을 하나의 API 방식으로 호출할 수 있게 해주는 서비스입니다.

쉽게 말하면, 이 프로젝트는 댓글을 직접 “이 댓글은 긍정인가요? 어떤 주제인가요?”라고 판단하지 않습니다. 대신 OpenRouter를 통해 AI 모델에게 분석을 요청합니다.

이 저장소에서는 [comment_analyzer.py](comment_analyzer.py)가 OpenRouter를 호출합니다.

```python
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "NPS_PR_Dashboard"
    }
)
```

여기서 중요한 점은 다음과 같습니다.

- Python 코드에서는 `openai` 패키지를 사용합니다.
- 하지만 실제 요청 주소는 OpenAI가 아니라 `https://openrouter.ai/api/v1`입니다.
- 그래서 OpenAI SDK와 비슷한 방식으로 OpenRouter를 호출할 수 있습니다.
- 어떤 모델을 쓸지는 `OPENROUTER_MODEL` 환경 변수로 정합니다.
- 기본 모델은 `openai/gpt-4o-mini`입니다.

### OpenRouter 사용 방법

OpenRouter를 이 프로젝트에서 쓰려면 아래 순서대로 준비하면 됩니다.

1. OpenRouter 웹사이트에 가입합니다.
2. 결제 또는 크레딧 메뉴에서 사용할 만큼의 credit을 충전합니다.
3. API Keys 메뉴에서 새 API key를 만듭니다.
4. 만든 API key를 로컬 `.env` 파일 또는 GitHub Secrets에 등록합니다.
5. `OPENROUTER_MODEL`에 사용할 모델 이름을 적습니다.
6. `python update_job.py` 또는 GitHub Actions를 통해 댓글 분석을 실행합니다.

로컬 `.env` 예시는 아래와 같습니다.

```text
OPENROUTER_API_KEY=여기에_OPENROUTER_API_키
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BATCH_SIZE=10
OPENROUTER_TIMEOUT=60
```

GitHub Actions에서는 `.env` 파일을 쓰지 않습니다. GitHub 저장소의 Secrets에 아래 이름으로 등록해야 합니다.

```text
OPENROUTER_API_KEY
```

이름이 정확히 같아야 `.github/workflows/update_data.yml`에서 값을 읽을 수 있습니다.

### AI 토큰과 비용

OpenRouter는 보통 **AI 토큰 사용량**을 기준으로 비용이 계산됩니다.

토큰은 AI 모델이 글을 읽고 쓸 때 사용하는 작은 텍스트 단위입니다. 한글의 경우 글자 수와 토큰 수가 정확히 1:1로 대응되지는 않지만, 쉽게 생각하면 “AI가 처리한 텍스트 조각의 양”이라고 보면 됩니다.

AI 모델을 호출하면 보통 아래 두 종류의 토큰이 비용에 영향을 줍니다.

- 입력 토큰: 프롬프트와 댓글 원문처럼 AI에게 보내는 내용
- 출력 토큰: AI가 감성, 카테고리, 키워드 JSON을 만들어 돌려주는 내용

즉, 댓글이 많거나 프롬프트가 길거나 출력이 길면 토큰 사용량이 늘어납니다. 토큰 사용량이 늘어나면 OpenRouter credit도 더 많이 소모됩니다.

OpenRouter는 모델마다 가격이 다릅니다. 큰 모델, 추론 모델, 고성능 모델은 비쌀 수 있고, 작은 모델은 상대적으로 저렴합니다. 최신 가격은 OpenRouter의 모델별 pricing 화면에서 확인해야 합니다.

### credit을 충전해서 써야 합니다

OpenRouter API는 일반적인 웹 구독형 챗봇과 다르게, API 호출 비용을 credit으로 차감하는 방식으로 이해하면 쉽습니다.

무료 모델이나 무료 사용량이 있을 수 있지만, 안정적으로 운영하려면 보통 OpenRouter 계정에 credit을 충전해 두는 편이 좋습니다. credit이 부족하면 GitHub Actions가 실행되어도 OpenRouter 분석 단계에서 실패할 수 있습니다.

관리자는 아래를 주기적으로 확인하는 것이 좋습니다.

- OpenRouter 계정에 남은 credit
- API key별 사용량
- API key별 credit limit
- 현재 사용 중인 모델의 토큰 단가
- GitHub Actions 로그의 OpenRouter 오류 여부

API key별 credit limit을 설정하면 실수로 너무 많은 비용이 나가는 것을 줄일 수 있습니다.

### 이 프로젝트의 OpenRouter 비용 감각

이 프로젝트는 댓글 감성, 주제, 키워드를 JSON으로 분류하는 작업입니다.

복잡한 장문 추론이나 고난도 코딩 작업이 아니기 때문에, 아주 큰 모델을 쓰지 않아도 충분히 운영할 수 있습니다. 기본값으로 둔 `openai/gpt-4o-mini` 같은 작은 모델 계열로도 대부분의 댓글 분류 작업은 충분히 처리됩니다.

또한 이 프로젝트는 **전체 댓글을 매번 다시 분석하지 않고 새 댓글만 분석**합니다.

이미 CSV에 저장된 댓글은 다시 OpenRouter로 보내지 않기 때문에, 운영 중 실제 credit 소모는 보통 다음 요소에 따라 작게 유지됩니다.

- 새로 달리는 댓글 수
- 프롬프트 길이
- `OPENROUTER_BATCH_SIZE`
- 선택한 모델의 토큰 단가

따라서 댓글이 폭발적으로 늘어나는 영상이 아니라면 많은 credit을 계속 소모하는 구조는 아닙니다. 소규모 모니터링 용도에서는 운영비가 비교적 낮게 유지될 가능성이 큽니다.

다만 AI 토큰 비용은 실제 사용량과 모델 가격에 따라 달라집니다. 운영자는 처음 며칠 동안 OpenRouter 사용량 화면을 확인하면서 어느 정도 credit이 소모되는지 감을 잡는 것이 좋습니다.

OpenRouter 공식 참고 링크:

- API 인증과 API key: https://openrouter.ai/docs/api/reference/authentication
- 모델별 가격: https://openrouter.ai/pricing
- 모델 pricing 구조: https://openrouter.ai/docs/guides/overview/models
- 요금과 credit 관련 FAQ: https://openrouter.ai/docs/faq

### OpenRouter가 필요한 이유

댓글 분석은 단순한 숫자 계산이 아닙니다. 댓글 문장을 읽고 맥락을 해석해야 합니다.

예를 들어 아래 댓글들이 있다고 가정합니다.

```text
국민연금 수익률이 이렇게 좋았다니 의외네요.
또 정치권이 개입하는 것 아닌가 걱정됩니다.
광고 문의는 여기로 연락 주세요.
```

AI 모델은 이런 댓글을 읽고 대략 아래처럼 분류합니다.

```csv
text,sentiment,category,keyword
국민연금 수익률이 이렇게 좋았다니 의외네요.,긍정,운용성과,수익률
또 정치권이 개입하는 것 아닌가 걱정됩니다.,부정,정부개입·거버넌스,정치권 개입
광고 문의는 여기로 연락 주세요.,광고,기타,광고
```

이 프로젝트는 이 분석 규칙을 `prompt/` 폴더의 프롬프트 파일에 적어 둡니다.

## YouTube Data API는 무엇인가요?

YouTube Data API는 유튜브 영상 정보와 댓글을 프로그램으로 가져올 수 있게 해주는 Google API입니다.

이 프로젝트에서는 [comment_collector.py](comment_collector.py)가 YouTube Data API를 호출합니다.

수집하는 정보는 크게 두 가지입니다.

- 댓글 목록: `commentThreads` API 사용
- 영상 통계: `videos` API 사용

영상 통계에는 조회수, 좋아요 수, 댓글 수, 영상 제목이 포함됩니다.

YouTube API를 사용하려면 `YOUTUBE_API_KEY`가 필요합니다. 이 값도 공개 저장소에 직접 쓰면 안 되며, 로컬에서는 `.env` 파일에, GitHub에서는 Secrets에 저장해야 합니다.

## 프로젝트 폴더 구조

현재 저장소의 주요 구조는 아래와 같습니다.

```text
.
├── index.html
├── dashboard_config.json
├── update_job.py
├── comment_collector.py
├── comment_analyzer.py
├── config_loader.py
├── reanalyze_existing_comments.py
├── requirements.txt
├── analyzed_comments/
│   ├── analyzed_comments_20260214.csv
│   ├── analyzed_comments_20260220.csv
│   └── analyzed_comments_20260423.csv
├── video_stats/
│   ├── video_stats_20260214.csv
│   ├── video_stats_20260220.csv
│   └── video_stats_20260423.csv
├── prompt/
│   ├── prompt_base.txt
│   ├── prompt_20260214.txt
│   ├── prompt_20260220.txt
│   └── prompt_20260423.txt
└── .github/
    └── workflows/
        └── update_data.yml
```

### `index.html`

대시보드 화면입니다.

브라우저가 이 파일을 열면 `dashboard_config.json`을 먼저 읽고, 그 설정에 맞춰 아래 CSV 파일들을 불러옵니다.

- `video_stats/video_stats_<start_date>.csv`
- `analyzed_comments/analyzed_comments_<start_date>.csv`

이 파일은 GitHub Pages를 통해 공개됩니다.

### `dashboard_config.json`

모니터링할 영상 목록과 대시보드 기본 설정을 담는 파일입니다.

어떤 영상을 보여줄지, 어떤 영상을 자동 수집할지, 어떤 프롬프트를 사용할지 이 파일에서 결정합니다.

### `update_job.py`

자동 업데이트의 중심 스크립트입니다.

GitHub Actions가 이 파일을 실행합니다. 로컬에서도 직접 실행할 수 있습니다.

이 파일이 하는 일은 다음과 같습니다.

1. `dashboard_config.json` 읽기
2. 수집 대상 영상 목록 확인
3. 영상 통계 수집
4. 댓글 수집
5. 기존 댓글과 비교해 새 댓글만 선별
6. 새 댓글을 OpenRouter로 분석
7. CSV 파일 저장

### `comment_collector.py`

YouTube Data API를 호출하는 파일입니다.

주요 함수는 다음과 같습니다.

- `fetch_youtube_comments(video_url)`: 영상 댓글을 가져옵니다.
- `fetch_video_stats(video_url)`: 조회수, 좋아요 수, 댓글 수를 가져옵니다.
- `extract_video_id(url)`: 유튜브 URL에서 영상 ID를 뽑습니다.

### `comment_analyzer.py`

OpenRouter를 통해 댓글을 분석하는 파일입니다.

주요 함수는 다음과 같습니다.

- `analyze_comments_with_llm(comments, prompt_template)`: 댓글 목록을 AI 모델로 분석합니다.
- `normalize_sentiment_label(sentiment)`: 감성 라벨을 정리합니다.
- `normalize_category_label(category)`: 주제 라벨을 정리합니다.

AI 응답은 JSON 형식으로 받도록 요청하고, 결과가 잘못 왔을 때는 댓글을 하나씩 다시 분석하는 재시도 로직도 들어 있습니다.

### `config_loader.py`

설정 파일을 읽고, 각 report에 필요한 파일 경로를 만들어 주는 파일입니다.

이 프로젝트는 데이터 파일을 폴더별로 정리했기 때문에, Python 스크립트는 직접 루트 경로의 CSV를 찾지 않습니다. 대신 `config_loader.py`의 helper 함수를 통해 파일 위치를 찾습니다.

- 댓글 분석 결과: `analyzed_comments/analyzed_comments_<start_date>.csv`
- 영상 통계: `video_stats/video_stats_<start_date>.csv`
- 프롬프트: `prompt/<prompt_file>`

`prompt_file`은 `dashboard_config.json`에서 `prompt/prompt_20260423.txt`처럼 전체 상대 경로로 적을 수 있습니다. 또는 `prompt_20260423.txt`처럼 파일명만 적어도 Python에서는 `prompt/` 폴더 안에서 찾도록 처리되어 있습니다.

### `reanalyze_existing_comments.py`

이미 저장된 댓글 CSV를 다시 분석할 때 사용하는 수동 스크립트입니다.

예를 들어 프롬프트 기준을 바꿨거나, 카테고리 체계를 정리하고 싶을 때 사용할 수 있습니다.

```bash
python reanalyze_existing_comments.py --report-id sampro_ceo_ep1_20260423
```

모든 활성 report를 다시 처리하려면 아래처럼 실행합니다.

```bash
python reanalyze_existing_comments.py --all
```

LLM을 다시 호출하지 않고 기존 라벨만 정규화하려면 아래 옵션을 씁니다.

```bash
python reanalyze_existing_comments.py --all --normalize-only
```

### `analyzed_comments/`

AI로 분석된 댓글 결과 CSV가 들어 있는 폴더입니다.

파일명 규칙은 다음과 같습니다.

```text
analyzed_comments/analyzed_comments_<start_date>.csv
```

예시:

```text
analyzed_comments/analyzed_comments_20260423.csv
```

CSV 컬럼은 아래 구조를 따릅니다.

```csv
text,sentiment,category,keyword
```

각 컬럼의 뜻은 다음과 같습니다.

- `text`: 댓글 원문
- `sentiment`: 감성 분류
- `category`: 주제 분류
- `keyword`: 핵심 키워드

### `video_stats/`

영상 통계 CSV가 들어 있는 폴더입니다.

파일명 규칙은 다음과 같습니다.

```text
video_stats/video_stats_<start_date>.csv
```

예시:

```text
video_stats/video_stats_20260423.csv
```

CSV 컬럼은 아래 구조를 따릅니다.

```csv
timestamp,view_count,like_count,comment_count,title
```

각 컬럼의 뜻은 다음과 같습니다.

- `timestamp`: 통계를 수집한 시각
- `view_count`: 조회수
- `like_count`: 좋아요 수
- `comment_count`: 댓글 수
- `title`: 영상 제목

### `prompt/`

OpenRouter에 보낼 분석 지시문이 들어 있는 폴더입니다.

공통 프롬프트는 아래 파일입니다.

```text
prompt/prompt_base.txt
```

영상별로 별도 기준이 필요하면 아래처럼 날짜가 들어간 파일을 둘 수 있습니다.

```text
prompt/prompt_20260423.txt
```

프롬프트에는 보통 다음 내용이 들어갑니다.

- 댓글을 어떤 감성 라벨로 나눌지
- 댓글을 어떤 주제 라벨로 나눌지
- 출력 JSON 형식은 어떻게 해야 하는지
- 광고나 무관한 댓글은 어떻게 처리할지

### `.github/workflows/update_data.yml`

GitHub Actions 자동 업데이트 설정 파일입니다.

이 파일은 아래 상황에서 실행됩니다.

- `main` 브랜치에 push가 발생했을 때
- 5분마다 한 번씩
- GitHub 화면에서 수동으로 실행했을 때

실행되면 아래 작업을 합니다.

1. 저장소 코드를 가져옵니다.
2. Python 3.10 환경을 준비합니다.
3. `requirements.txt`의 라이브러리를 설치합니다.
4. GitHub Secrets에서 API 키를 환경 변수로 불러옵니다.
5. `python update_job.py`를 실행합니다.
6. 변경된 `analyzed_comments/`, `video_stats/`, `prompt/`, `dashboard_config.json`을 Git에 추가합니다.
7. 변경이 있으면 `Auto-update data` 커밋을 만들고 push합니다.

## 설정 파일 자세히 보기

모든 영상 메타데이터는 [dashboard_config.json](dashboard_config.json)에서 관리합니다.

현재 구조는 아래와 같습니다.

```json
{
  "dashboard_title": "국민연금 이사장 유튜브 여론 모니터링",
  "default_report_id": "sampro_ceo_ep1_20260423",
  "default_prompt_file": "prompt/prompt_base.txt",
  "reports": [
    {
      "id": "sampro_ceo_ep1_20260423",
      "tab_label": "지식인사이드",
      "video_title": "영상 제목",
      "video_url": "https://youtu.be/...",
      "start_date": "20260423",
      "video_start_at": "2026-04-23 19:00:00",
      "prompt_file": "prompt/prompt_20260423.txt",
      "enabled": true,
      "collect_enabled": true
    }
  ]
}
```

### 최상위 필드

`dashboard_title`은 대시보드 상단 제목입니다.

`default_report_id`는 대시보드를 처음 열었을 때 기본으로 보여줄 report입니다. 현재 대시보드는 가장 최신 영상 탭을 자동으로 활성화하지만, 기본 report 식별자는 수동 작업이나 코드 이해에 여전히 중요합니다.

`default_prompt_file`은 개별 report에 `prompt_file`이 없을 때 사용할 기본 프롬프트입니다.

`reports`는 영상 목록입니다. 영상 하나가 report 하나입니다.

### report 필드

`id`는 report의 내부 식별자입니다.

예시:

```json
"id": "sampro_ceo_ep1_20260423"
```

스크립트에서 특정 영상을 지정할 때 이 값을 사용합니다.

```bash
python reanalyze_existing_comments.py --report-id sampro_ceo_ep1_20260423
```

`tab_label`은 대시보드 탭에 표시되는 짧은 이름입니다.

`video_title`은 화면에 표시할 영상 제목입니다. YouTube API에서도 제목을 가져오지만, 사람이 읽기 좋은 기준 제목을 설정 파일에 적어 둡니다.

`video_url`은 실제 유튜브 영상 주소입니다.

`start_date`는 파일명을 만들 때 사용하는 날짜 키입니다.

예를 들어 아래처럼 설정되어 있으면:

```json
"start_date": "20260423"
```

Python과 대시보드는 아래 파일을 사용합니다.

```text
analyzed_comments/analyzed_comments_20260423.csv
video_stats/video_stats_20260423.csv
prompt/prompt_20260423.txt
```

`video_start_at`은 영상이 공개되었거나 모니터링 기준으로 삼을 시작 시각입니다.

통계 CSV가 비어 있거나 첫 수집 시점이 늦을 경우, 대시보드는 이 시각을 기준으로 0에서 시작하는 행을 만들어 조회수 추이를 자연스럽게 보여줍니다.

`prompt_file`은 해당 영상 분석에 사용할 프롬프트 파일입니다.

현재는 명확하게 보이도록 `prompt/prompt_20260423.txt`처럼 폴더까지 적습니다. Python 쪽은 파일명만 적어도 `prompt/` 폴더에서 찾도록 되어 있지만, 새로 추가할 때는 폴더까지 적는 방식을 권장합니다.

`enabled`가 `true`이면 대시보드에 표시됩니다.

`collect_enabled`가 `true`이면 GitHub Actions가 이 영상을 자동 수집합니다.

### `enabled`와 `collect_enabled`의 차이

둘은 비슷해 보이지만 역할이 다릅니다.

`enabled`는 화면 표시 여부입니다.

`collect_enabled`는 자동 수집 여부입니다.

예를 들어 과거 영상을 대시보드에는 계속 보여주되 더 이상 새 댓글을 수집하지 않고 싶다면 아래처럼 설정할 수 있습니다.

```json
{
  "enabled": true,
  "collect_enabled": false
}
```

반대로 아직 준비 중인 영상을 화면에 숨기고 싶다면 아래처럼 둘 수 있습니다.

```json
{
  "enabled": false,
  "collect_enabled": false
}
```

## 파일명 규칙

이 프로젝트는 `start_date`를 기준으로 데이터 파일을 연결합니다.

예를 들어 report의 `start_date`가 `20260423`이면 관련 파일은 아래와 같습니다.

```text
analyzed_comments/analyzed_comments_20260423.csv
video_stats/video_stats_20260423.csv
prompt/prompt_20260423.txt
```

이 규칙이 중요한 이유는 코드가 파일명을 자동으로 만들기 때문입니다.

[config_loader.py](config_loader.py)는 아래 방식으로 파일 경로를 만듭니다.

```python
def data_file_for_report(report: dict) -> str:
    return str(ANALYZED_COMMENTS_DIR / f"analyzed_comments_{report['start_date']}.csv")

def stats_file_for_report(report: dict) -> str:
    return str(VIDEO_STATS_DIR / f"video_stats_{report['start_date']}.csv")
```

따라서 새 영상을 추가할 때는 `start_date` 값을 신중하게 정해야 합니다. 한 번 정한 뒤 나중에 바꾸면 기존 CSV 파일명과 연결이 끊길 수 있습니다.

## 새 영상 추가 방법

새 유튜브 영상을 모니터링하려면 아래 순서대로 진행합니다.

### 1. 영상 정보 정리

먼저 아래 정보를 준비합니다.

- 유튜브 URL
- 대시보드 탭에 표시할 이름
- 영상 제목
- 영상 공개 시각 또는 모니터링 시작 시각
- 파일명에 사용할 날짜 키

날짜 키는 보통 `YYYYMMDD` 형식을 사용합니다.

예시:

```text
20260710
```

### 2. 프롬프트 결정

기존 분석 기준을 그대로 쓸 수 있으면 `prompt/prompt_base.txt`를 사용해도 됩니다.

영상별로 다른 맥락이나 다른 분류 기준이 필요하면 새 프롬프트 파일을 만듭니다.

예시:

```text
prompt/prompt_20260710.txt
```

새 프롬프트를 만들 때는 기존 `prompt/prompt_20260423.txt` 같은 파일을 참고해 형식을 맞추는 것이 좋습니다.

### 3. `dashboard_config.json`에 report 추가

`reports` 배열에 새 항목을 추가합니다.

예시:

```json
{
  "id": "new_video_20260710",
  "tab_label": "새 영상",
  "video_title": "새로 모니터링할 영상 제목",
  "video_url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
  "start_date": "20260710",
  "video_start_at": "2026-07-10 09:00:00",
  "prompt_file": "prompt/prompt_20260710.txt",
  "enabled": true,
  "collect_enabled": true
}
```

### 4. 로컬에서 한 번 실행해 보기

API 키가 준비되어 있다면 로컬에서 아래 명령을 실행합니다.

```bash
python update_job.py
```

정상 실행되면 아래 파일이 생기거나 갱신됩니다.

```text
analyzed_comments/analyzed_comments_20260710.csv
video_stats/video_stats_20260710.csv
```

### 5. 대시보드 확인

로컬에서 대시보드를 확인하려면 단순히 `index.html`을 더블클릭하는 것보다 간단한 웹 서버로 여는 편이 안전합니다.

```bash
python -m http.server 8000
```

그 다음 브라우저에서 아래 주소를 엽니다.

```text
http://localhost:8000
```

브라우저 보안 정책 때문에 로컬 파일을 직접 여는 방식은 `dashboard_config.json`이나 CSV fetch가 실패할 수 있습니다.

### 6. GitHub에 반영

변경된 파일을 커밋하고 push하면 GitHub Pages와 GitHub Actions에 반영됩니다.

일반적인 흐름은 아래와 같습니다.

```bash
git status
git add dashboard_config.json prompt/ analyzed_comments/ video_stats/
git commit -m "Add new monitored video"
git push origin main
```

## 다른 사람이 이 저장소를 clone해서 사용하는 방법

이 프로젝트는 다른 사람이 그대로 가져가서 자기 영상 모니터링 시스템으로 바꾸기 좋게 구성되어 있습니다.

GitHub에서 `clone`한다는 것은 인터넷에 있는 저장소를 내 컴퓨터로 복사한다는 뜻입니다.

```bash
git clone https://github.com/roy8in/youtube-comment-monitoring.git
cd youtube-comment-monitoring
```

이렇게 하면 현재 저장소의 코드, README, 대시보드, 자동화 설정, 프롬프트, CSV 구조가 내 컴퓨터에 그대로 내려옵니다.

### clone하면 무엇이 편리한가요?

처음부터 직접 만들려면 아래 작업을 모두 해야 합니다.

- 유튜브 댓글 수집 코드 작성
- 유튜브 영상 통계 수집 코드 작성
- AI 분석 프롬프트 작성
- OpenRouter 호출 코드 작성
- 중복 댓글 제거 로직 작성
- CSV 저장 규칙 설계
- 대시보드 HTML과 차트 구성
- GitHub Actions 자동 실행 설정
- GitHub Pages 공개 설정
- API Key를 안전하게 관리하는 구조 설계

이 저장소를 clone하면 위 기반 작업이 이미 들어 있습니다.

사용자는 보통 아래만 바꾸면 됩니다.

- `dashboard_config.json`의 영상 URL과 제목
- `prompt/` 폴더의 분석 기준
- 본인의 `YOUTUBE_API_KEY`
- 본인의 `OPENROUTER_API_KEY`
- 필요하다면 대시보드 제목과 탭 이름

즉, 이 저장소는 **유튜브 댓글 여론 모니터링용 템플릿**처럼 사용할 수 있습니다. 국민연금 관련 영상뿐 아니라, 다른 기관, 브랜드, 캠페인, 강연, 정책 홍보, 제품 리뷰 영상에도 구조를 바꿔 적용할 수 있습니다.

### clone과 fork의 차이

단순히 내 컴퓨터에서 실행해 보려면 `clone`만 해도 됩니다.

하지만 본인의 GitHub 계정에서 GitHub Actions와 GitHub Pages까지 운영하려면 보통 `fork`하거나 새 저장소를 만들어야 합니다.

`clone`은 저장소를 내 컴퓨터로 내려받는 작업입니다.

`fork`는 GitHub 안에서 다른 사람의 저장소를 내 계정 아래로 복사하는 작업입니다.

이 프로젝트를 자기 계정에서 계속 운영하려면 보통 아래 흐름을 권장합니다.

1. GitHub에서 이 저장소를 fork합니다.
2. fork된 내 저장소를 clone합니다.
3. `dashboard_config.json`을 내 영상 목록에 맞게 수정합니다.
4. `prompt/`의 프롬프트를 내 분석 목적에 맞게 수정합니다.
5. GitHub Secrets에 `YOUTUBE_API_KEY`, `OPENROUTER_API_KEY`를 등록합니다.
6. GitHub Pages를 켭니다.
7. 변경사항을 commit하고 push합니다.
8. GitHub Actions가 자동으로 데이터를 수집하는지 확인합니다.

### clone 후 로컬에서 먼저 테스트하는 흐름

아래 순서로 하면 GitHub에 올리기 전에 내 컴퓨터에서 먼저 확인할 수 있습니다.

```bash
git clone https://github.com/roy8in/youtube-comment-monitoring.git
cd youtube-comment-monitoring
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

그 다음 `.env` 파일을 만들고 API Key를 넣습니다.

```text
YOUTUBE_API_KEY=본인의_유튜브_API_키
OPENROUTER_API_KEY=본인의_OPENROUTER_API_키
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BATCH_SIZE=10
OPENROUTER_TIMEOUT=60
```

그리고 설정 파일을 수정합니다.

```text
dashboard_config.json
prompt/prompt_base.txt
```

데이터 수집과 분석을 실행합니다.

```bash
python update_job.py
```

대시보드를 확인합니다.

```bash
python -m http.server 8000
```

브라우저에서 아래 주소를 엽니다.

```text
http://localhost:8000
```

macOS나 일부 Linux 환경에서 `python` 명령이 없으면 `python3`를 사용하면 됩니다.

### 자기 GitHub 저장소로 연결해서 운영하기

clone한 저장소를 본인의 새 GitHub 저장소에 연결하려면 `origin` 원격 주소를 바꿔야 합니다.

현재 원격 주소는 아래 명령으로 확인할 수 있습니다.

```bash
git remote -v
```

본인의 새 저장소 주소로 바꾸려면 아래처럼 실행합니다.

```bash
git remote set-url origin https://github.com/내계정/내저장소이름.git
git push origin main
```

그 다음 GitHub 웹사이트에서 아래를 설정합니다.

- Repository Secrets에 `YOUTUBE_API_KEY` 등록
- Repository Secrets에 `OPENROUTER_API_KEY` 등록
- GitHub Pages 설정
- Actions 탭에서 workflow 실행 상태 확인

여기까지 완료하면, 본인 저장소에서도 같은 방식으로 자동 업데이트되는 댓글 모니터링 대시보드를 운영할 수 있습니다.

## 로컬 개발 환경 준비

로컬 컴퓨터에서 직접 수집과 분석을 실행하려면 Python 환경과 API 키가 필요합니다.

아래 예시는 `python` 명령을 사용합니다. macOS나 일부 Linux 환경에서 `python: command not found`가 나오면 같은 자리에 `python3`를 사용하면 됩니다.

### 1. 저장소 최신화

작업 전에는 GitHub의 최신 변경사항을 가져옵니다.

```bash
git pull --ff-only origin main
```

### 2. Python 가상환경 만들기

이미 가상환경이 있다면 이 단계는 건너뛰어도 됩니다.

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell에서는 보통 아래처럼 활성화합니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 4. `.env` 파일 만들기

로컬 실행용 API 키는 프로젝트 루트의 `.env` 파일에 넣습니다.

```text
YOUTUBE_API_KEY=여기에_유튜브_API_키
OPENROUTER_API_KEY=여기에_OPENROUTER_API_키
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BATCH_SIZE=10
OPENROUTER_TIMEOUT=60
```

`.env` 파일은 GitHub에 올리면 안 됩니다. API 키가 외부에 공개되면 비용이 발생하거나 키가 악용될 수 있습니다.

### 5. 업데이트 실행

```bash
python update_job.py
```

### 6. 대시보드 실행

```bash
python -m http.server 8000
```

브라우저에서 아래 주소를 엽니다.

```text
http://localhost:8000
```

## GitHub Actions 자동 업데이트

자동 업데이트는 [.github/workflows/update_data.yml](.github/workflows/update_data.yml)이 담당합니다.

현재 설정은 아래 조건에서 실행됩니다.

```yaml
on:
  push:
    branches:
      - main
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:
```

각 의미는 다음과 같습니다.

- `push`: `main` 브랜치에 변경사항이 올라오면 실행
- `schedule`: 5분마다 실행
- `workflow_dispatch`: GitHub Actions 화면에서 사람이 직접 실행 가능

실제 실행 명령의 핵심은 아래 부분입니다.

```yaml
- name: 데이터 업데이트 및 결과 저장
  env:
    YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    OPENROUTER_MODEL: openai/gpt-4o-mini
    OPENROUTER_BATCH_SIZE: 10
    OPENROUTER_TIMEOUT: 60
    TZ: Asia/Seoul
  run: |
    git config --global user.name 'github-actions[bot]'
    git config --global user.email 'github-actions[bot]@users.noreply.github.com'
    git pull --rebase origin main
    python update_job.py
    git add analyzed_comments/ video_stats/ prompt/ dashboard_config.json
    git diff --quiet && git diff --staged --quiet || (git commit -m "Auto-update data" && git push)
```

여기서 중요한 점은 API 키를 파일에 적지 않고 GitHub Secrets에서 가져온다는 것입니다.

또한 자동 커밋 대상은 새 폴더 구조에 맞춰 아래로 정리되어 있습니다.

- `analyzed_comments/`
- `video_stats/`
- `prompt/`
- `dashboard_config.json`

## GitHub Secrets 설정 방법

GitHub Actions가 YouTube API와 OpenRouter를 호출하려면 저장소에 secret을 등록해야 합니다.

GitHub 웹사이트에서 보통 아래 경로로 이동합니다.

```text
Repository > Settings > Secrets and variables > Actions > New repository secret
```

등록해야 하는 secret은 아래 두 개입니다.

```text
YOUTUBE_API_KEY
OPENROUTER_API_KEY
```

이름은 정확히 일치해야 합니다. 대소문자도 중요합니다.

## 수동 실행 명령 모음

전체 자동 업데이트를 로컬에서 한 번 실행:

```bash
python update_job.py
```

특정 report의 기존 댓글을 다시 분석:

```bash
python reanalyze_existing_comments.py --report-id sampro_ceo_ep1_20260423
```

모든 활성 report의 기존 댓글을 다시 분석:

```bash
python reanalyze_existing_comments.py --all
```

LLM 호출 없이 기존 CSV의 감성/카테고리 라벨만 정리:

```bash
python reanalyze_existing_comments.py --all --normalize-only
```

로컬 웹 서버 실행:

```bash
python -m http.server 8000
```

현재 Git 상태 확인:

```bash
git status
```

GitHub 최신 변경사항 가져오기:

```bash
git pull --ff-only origin main
```

## 댓글 분석 방식 자세히 보기

댓글 분석은 [comment_analyzer.py](comment_analyzer.py)에서 처리합니다.

분석 과정은 아래와 같습니다.

1. 새 댓글 목록을 일정 개수씩 묶습니다.
2. 프롬프트 파일 내용을 읽습니다.
3. 프롬프트 뒤에 엄격한 출력 규칙을 추가합니다.
4. OpenRouter에 JSON 형식 응답을 요청합니다.
5. 응답의 `data` 배열 길이가 입력 댓글 수와 같은지 확인합니다.
6. 감성 라벨과 카테고리 라벨을 정규화합니다.
7. 결과를 CSV에 저장할 수 있는 dict 목록으로 반환합니다.

프롬프트에는 사람이 작성한 분석 기준이 들어 있고, 코드에서는 추가로 아래 원칙을 강제합니다.

- 입력 댓글 1개는 출력 행 1개여야 합니다.
- 여러 댓글을 합치면 안 됩니다.
- 댓글 하나를 여러 행으로 쪼개면 안 됩니다.
- 출력 순서는 입력 순서와 같아야 합니다.
- `text` 값은 입력 댓글 원문과 같아야 합니다.

그래도 AI 응답이 가끔 형식을 어길 수 있기 때문에, 배치 분석이 실패하면 댓글을 하나씩 다시 분석하는 로직이 들어 있습니다.

## 중복 댓글을 피하는 방식

[update_job.py](update_job.py)는 기존 CSV에 있는 댓글을 다시 분석하지 않습니다.

비교할 때는 공백 차이 때문에 중복 판단이 흔들리지 않도록, 댓글 문자열의 공백을 제거한 값으로 비교합니다.

```python
def normalize(text):
    return "".join(text.split()) if isinstance(text, str) else ""
```

예를 들어 아래 두 댓글은 같은 댓글로 취급됩니다.

```text
국민연금 수익률 좋네요
국민연금   수익률   좋네요
```

이렇게 하면 OpenRouter 비용을 줄이고, 기존 분석 결과가 중복으로 쌓이는 문제를 줄일 수 있습니다.

## 카테고리와 감성 라벨

감성 라벨은 아래 값으로 정리됩니다.

- `긍정`
- `중립`
- `부정`
- `광고`
- `오류`

AI가 `기타`처럼 애매한 값을 반환하면 현재 코드는 대체로 `중립`으로 정리합니다.

OpenRouter 호출 실패, 응답 형식 오류, 분석 결과 누락처럼 운영자가 확인해야 하는 문제는 `오류`로 남깁니다. 이렇게 해야 대시보드와 CSV에서 분석 실패를 `중립` 댓글로 오해하지 않을 수 있습니다.

카테고리 라벨은 [comment_analyzer.py](comment_analyzer.py)의 `CATEGORY_ALIAS_MAP`에서 정리합니다.

예를 들어 AI가 `기금수익`이라고 반환하면 대시보드에서는 `운용성과`로 묶입니다.

이 매핑은 대시보드의 집계 품질에 영향을 주기 때문에, 새 카테고리를 추가할 때는 프롬프트와 `CATEGORY_ALIAS_MAP`을 함께 확인하는 것이 좋습니다.

## 데이터 파일을 직접 수정할 때 주의할 점

CSV를 직접 수정할 수는 있지만 아래를 지켜야 합니다.

- CSV 헤더를 바꾸지 마세요.
- `text` 컬럼은 댓글 원문을 유지하는 것이 좋습니다.
- `sentiment` 값은 `긍정`, `중립`, `부정`, `광고`, `오류` 중 하나로 맞추는 것이 좋습니다.
- `category` 값은 대시보드에서 의미 있게 묶일 수 있는 값으로 맞춰야 합니다.
- Excel에서 열었다가 저장하면 인코딩이나 줄바꿈이 깨질 수 있으니 주의해야 합니다.

가능하면 CSV를 수동 편집하기보다 `reanalyze_existing_comments.py`를 사용하는 편이 안전합니다.

## 프롬프트를 수정할 때 주의할 점

프롬프트는 AI 분석 결과를 크게 바꿀 수 있습니다.

프롬프트를 수정할 때는 아래를 확인하세요.

- 감성 라벨 이름이 코드의 정규화 함수와 맞는가
- 카테고리 라벨 이름이 `CATEGORY_ALIAS_MAP`과 맞는가
- JSON 출력 형식이 유지되는가
- 댓글 원문을 바꾸지 말라는 지시가 들어 있는가
- 광고, 욕설, 무관한 댓글 처리 기준이 명확한가

프롬프트를 바꾼 뒤 이미 저장된 댓글까지 새 기준으로 맞추려면 재분석을 실행해야 합니다.

```bash
python reanalyze_existing_comments.py --report-id sampro_ceo_ep1_20260423
```

## 대시보드가 데이터를 읽는 방식

[index.html](index.html)은 서버에서 별도 API를 호출하지 않습니다.

브라우저가 정적 파일을 직접 읽습니다.

1. `dashboard_config.json`을 읽습니다.
2. `reports` 목록에서 `enabled !== false`인 report만 고릅니다.
3. 각 report의 `start_date`로 CSV 경로를 만듭니다.
4. `video_stats/video_stats_<start_date>.csv`를 읽습니다.
5. `analyzed_comments/analyzed_comments_<start_date>.csv`를 읽습니다.
6. JavaScript가 브라우저 안에서 차트와 표를 만듭니다.

이 구조의 장점은 서버 운영이 필요 없다는 것입니다.

단점은 CSV 경로가 틀리거나 파일이 없으면 대시보드가 데이터를 불러오지 못할 수 있다는 점입니다. 새 영상을 추가했다면 최소 한 번은 `update_job.py`를 실행해 CSV 파일이 만들어졌는지 확인하세요.

## 자주 하는 작업

### 자동 수집 대상에서 잠시 제외하기

`dashboard_config.json`에서 해당 report를 찾아 아래처럼 바꿉니다.

```json
"collect_enabled": false
```

대시보드에는 계속 보이지만 새 데이터 수집은 멈춥니다.

### 대시보드에서 숨기기

```json
"enabled": false
```

이 경우 화면에서 보이지 않습니다.

### 기본 프롬프트 바꾸기

`prompt/prompt_base.txt`를 수정합니다.

특정 영상만 다르게 분석하고 싶다면 그 영상의 `prompt_file`을 별도 파일로 지정합니다.

```json
"prompt_file": "prompt/prompt_20260710.txt"
```

### 자동 업데이트 주기 바꾸기

`.github/workflows/update_data.yml`의 cron 값을 수정합니다.

현재 값:

```yaml
- cron: '*/5 * * * *'
```

이 값은 5분마다 실행한다는 뜻입니다.

예를 들어 1시간마다 실행하려면 아래처럼 바꿀 수 있습니다.

```yaml
- cron: '0 * * * *'
```

GitHub Actions의 scheduled workflow는 정확히 초 단위로 실행되는 스케줄러가 아니며, GitHub 상황에 따라 지연될 수 있습니다.

## 디버깅과 운영 로그

자동 업데이트가 실패하거나 예상과 다르게 동작할 때는 먼저 GitHub Actions 로그를 확인합니다.

GitHub 웹사이트에서 보통 아래 경로로 이동합니다.

```text
Repository > Actions > Auto Update YouTube PR Data > 실패한 실행 선택
```

이 프로젝트는 운영 중 원인을 찾기 쉽도록 Python의 `logging`을 사용합니다.

기본 로그 레벨은 `INFO`입니다. 더 자세한 로그가 필요하면 로컬 실행이나 GitHub Actions 환경 변수에서 아래처럼 설정할 수 있습니다.

```text
LOG_LEVEL=DEBUG
```

DEBUG 로그에서는 YouTube API 요청의 endpoint와 key가 가려진 요청 파라미터, 댓글 페이지 수집 진행 상황, OpenRouter 원본 응답 일부가 추가로 표시됩니다.

API Key는 로그에 직접 출력하지 않도록 처리되어 있습니다.

### 주요 로그에서 확인할 것

`댓글 수집 완료` 로그는 YouTube에서 댓글을 몇 개 가져왔는지 보여줍니다.

`댓글 비교 완료` 로그는 전체 수집 댓글, 기존 댓글, 신규 댓글 수를 보여줍니다.

`OpenRouter 배치 분석 시작` 로그는 어떤 모델로 몇 번째 배치를 분석하는지 보여줍니다.

`OpenRouter 배치 분석 실패 후 단건 재시도` 로그가 보이면 AI 응답 형식이 기대와 달라서 댓글 하나씩 다시 분석했다는 뜻입니다.

`업데이트 요약` 로그는 전체 report 중 성공과 실패 개수를 보여줍니다.

### 디버깅에 유용한 환경 변수

```text
LOG_LEVEL=INFO
YOUTUBE_API_TIMEOUT=30
OPENROUTER_TIMEOUT=60
OPENROUTER_BATCH_SIZE=10
```

`LOG_LEVEL`은 로그 상세도를 조절합니다. 일반 운영은 `INFO`, 원인 분석은 `DEBUG`를 사용합니다.

`YOUTUBE_API_TIMEOUT`은 YouTube API 응답을 기다릴 최대 시간입니다.

`OPENROUTER_TIMEOUT`은 OpenRouter 응답을 기다릴 최대 시간입니다.

`OPENROUTER_BATCH_SIZE`는 한 번에 몇 개 댓글을 AI 모델로 분석할지 정합니다. 값이 너무 크면 응답 형식 오류나 timeout이 늘 수 있고, 너무 작으면 호출 횟수와 비용이 늘 수 있습니다.

### 일부 report 실패 처리

`update_job.py`는 한 report에서 오류가 나도 가능한 경우 다음 report까지 계속 확인합니다.

마지막에는 실패한 report 목록을 요약하고, 실패가 있으면 GitHub Actions 실행을 실패 상태로 끝냅니다. 이렇게 하면 조용히 실패를 숨기지 않고 Actions 화면에서 바로 문제를 확인할 수 있습니다.

## 문제 해결

### `YOUTUBE_API_KEY` 오류가 나는 경우

로컬에서는 `.env` 파일에 `YOUTUBE_API_KEY`가 있는지 확인하세요.

GitHub Actions에서는 repository secret에 `YOUTUBE_API_KEY`가 등록되어 있는지 확인하세요.

### `OPENROUTER_API_KEY` 오류가 나는 경우

로컬에서는 `.env` 파일에 `OPENROUTER_API_KEY`가 있는지 확인하세요.

GitHub Actions에서는 repository secret에 `OPENROUTER_API_KEY`가 등록되어 있는지 확인하세요.

### 대시보드가 CSV를 읽지 못하는 경우

아래 파일이 실제로 존재하는지 확인하세요.

```text
analyzed_comments/analyzed_comments_<start_date>.csv
video_stats/video_stats_<start_date>.csv
```

그리고 `dashboard_config.json`의 `start_date`와 파일명 날짜가 같은지 확인하세요.

### 새 댓글이 있는데 분석이 안 되는 경우

확인할 항목은 다음과 같습니다.

- `collect_enabled`가 `true`인가
- YouTube API 키가 정상인가
- OpenRouter API 키가 정상인가
- `prompt_file` 경로가 올바른가
- GitHub Actions 로그에 오류가 있는가

### GitHub Actions가 커밋하지 않는 경우

데이터에 변경이 없으면 커밋하지 않는 것이 정상입니다.

워크플로 마지막 줄은 변경사항이 있을 때만 커밋합니다.

```bash
git diff --quiet && git diff --staged --quiet || (git commit -m "Auto-update data" && git push)
```

즉, 새 댓글이나 새 통계 행이 없다면 아무 커밋도 생기지 않을 수 있습니다.

### OpenRouter 응답 형식 오류가 나는 경우

AI 모델이 JSON 형식을 제대로 지키지 못했을 가능성이 있습니다.

이 경우 코드는 배치 전체를 실패 처리하지 않고 댓글 단위로 재시도합니다. 그래도 실패하면 해당 댓글은 `sentiment`가 `오류`, `keyword`에 에러 종류가 들어갈 수 있습니다.

프롬프트가 너무 복잡하거나 출력 형식 지시가 약하면 오류가 늘어날 수 있으니 프롬프트를 점검하세요.

## 관리자가 기억하면 좋은 원칙

이 프로젝트는 설정 파일과 파일명 규칙이 연결되어 있습니다.

따라서 아래 원칙을 지키면 문제가 줄어듭니다.

- `dashboard_config.json`의 `start_date`와 CSV 파일명 날짜를 맞춥니다.
- 프롬프트 파일은 `prompt/` 폴더에 둡니다.
- 분석 댓글 CSV는 `analyzed_comments/` 폴더에 둡니다.
- 영상 통계 CSV는 `video_stats/` 폴더에 둡니다.
- API 키는 절대 코드나 README에 직접 쓰지 않습니다.
- 새 영상을 추가한 뒤에는 로컬 또는 GitHub Actions에서 한 번 실행해 CSV가 생성되는지 확인합니다.
- 프롬프트를 바꿨다면 기존 댓글을 재분석해야 결과 기준이 맞습니다.
- 자동 업데이트가 만든 CSV 변경사항은 GitHub 커밋 이력에 남습니다.

## 빠른 체크리스트

새로운 사람이 프로젝트를 이어받았다면 아래 순서로 확인하면 됩니다.

1. GitHub 저장소 주소를 확인합니다.
2. GitHub Pages 대시보드가 열리는지 확인합니다.
3. `dashboard_config.json`에서 현재 영상 목록을 확인합니다.
4. `analyzed_comments/`와 `video_stats/`에 CSV가 있는지 확인합니다.
5. `prompt/`에서 분석 기준을 확인합니다.
6. GitHub Secrets에 `YOUTUBE_API_KEY`, `OPENROUTER_API_KEY`가 등록되어 있는지 확인합니다.
7. Actions 탭에서 `Auto Update YouTube PR Data`가 성공적으로 실행되는지 확인합니다.
8. 로컬에서 작업할 경우 `.env`를 만들고 `python update_job.py`를 실행해 봅니다.
9. 변경 후 `python -m http.server 8000`으로 대시보드를 확인합니다.
10. 문제가 없으면 commit 후 push합니다.
