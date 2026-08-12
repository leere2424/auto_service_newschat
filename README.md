# 뉴스 요약 CLI 챗봇

매일 한국경제(한경)의 IT·경제 뉴스를 골라 **요약·시사점·질문**으로 정리해 Notion에 저장하고,
그날 저장된 질문들을 놓고 CLI에서 AI와 대화하며 생각을 정리하는 프로젝트입니다.

- **수집·정리** — n8n 워크플로우가 매일 뉴스를 가져와 OpenAI로 요약하고 Notion DB에 기록
- **대화** — [chat.py](chat.py)가 오늘 자 Notion 레코드를 읽어와, 그 맥락 위에서 질문을 던지고 반문해 주는 대화 파트너 역할

## 기술 스택

| 영역 | 사용 기술 |
| --- | --- |
| 언어 | Python 3.10+ |
| LLM | OpenAI API (`gpt-4o-mini`) |
| 저장소 | Notion API (`notion-client`) |
| 자동화 | n8n (일일 뉴스 수집·요약 워크플로우) |

## 동작 흐름

```
한국경제 IT·경제 뉴스
        │
        ▼
   n8n 워크플로우 (매일 실행)
   기사 선별 → OpenAI 요약/시사점/질문 생성
        │
        ▼
     Notion DB  (날짜 · 분류 · 제목 · 요약 · 시사점 · 질문)
        │
        ▼
     chat.py (CLI)
   오늘 자 뉴스 로드 → 질문 제시 → AI와 대화
```

## 시작하기

### 1. 설치

```bash
git clone <repository-url>
cd auto_service_newschat

python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```

### 2. 환경 변수

프로젝트 루트에 `.env` 파일을 만들고 아래 값을 채웁니다. (`.env`는 [.gitignore](.gitignore)로 커밋에서 제외됩니다.)

```env
OPENAI_API_KEY=sk-...
NOTION_TOKEN=ntn_...
NOTION_DB_ID=...
```

| 변수 | 설명 |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `NOTION_TOKEN` | Notion 내부 통합(Integration) 토큰 |
| `NOTION_DB_ID` | 뉴스가 저장되는 Notion 데이터베이스 ID |

> Notion 통합을 만든 뒤, 대상 데이터베이스 페이지에서 해당 통합을 **연결(Connect)** 해 두어야 API로 읽을 수 있습니다.

### 3. Notion 데이터베이스 구조

`chat.py`는 아래 속성 이름을 그대로 사용합니다. 이름이 다르면 조회에 실패합니다.

| 속성 | 타입 | 설명 |
| --- | --- | --- |
| `날짜` | Date | 뉴스 저장 일자 (오늘 자 필터 기준) |
| `분류` | Select | IT / 경제 등 카테고리 |
| `제목` | Title | 기사 제목 |
| `요약` | Rich text | 기사 요약 |
| `시사점` | Rich text | 기사에서 끌어낸 시사점 |
| `질문` | Rich text | 사용자에게 던지는 생각 질문 |

### 4. 실행

```bash
python chat.py
```

```
오늘의 뉴스를 불러오는 중...

[IT] 국내 반도체 기업, 차세대 HBM 양산 발표
  질문: 이 경쟁이 국내 부품 생태계에 어떤 영향을 줄까요?

==================================================
위 질문에 대해 생각을 나눠봐요. (끝내려면 quit 입력)
==================================================

나: _
```

`quit`, `exit`, `종료` 중 하나를 입력하면 대화가 끝납니다.

## 구성 요소

| 파일 | 역할 |
| --- | --- |
| [chat.py](chat.py) | 오늘 자 뉴스 조회 → 맥락 구성 → CLI 대화 루프 |
| [requirements.txt](requirements.txt) | Python 의존성 |

주요 함수

- `fetch_today_news()` — Notion DB에서 오늘 0시 ~ 내일 0시 사이의 레코드만 조회
- `build_context(news)` — 뉴스 목록을 LLM 시스템 프롬프트용 텍스트로 조립
- `main()` — 오늘의 질문을 출력하고 대화 루프 실행

## 참고

- n8n 워크플로우는 이 저장소에 포함되어 있지 않으며, n8n 인스턴스에서 별도로 관리합니다.
- "오늘 저장된 뉴스가 없어요"가 출력되면 n8n 워크플로우가 그날 실행됐는지 먼저 확인하세요.
- Notion API의 데이터소스(data source) 조회 방식을 사용하므로 `notion-client` 3.x 이상이 필요합니다.

### GitHub MCP + n8n MCP 연동
**커밋(로컬 git) + 이슈 관리(GitHub MCP)**가 다 자연어로 가능하다.
-> 커밋·이슈 자동화 완료
