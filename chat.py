import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from notion_client import Client

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
notion = Client(auth=os.getenv("NOTION_TOKEN"))
DB_ID = os.getenv("NOTION_DB_ID")


def get_text(prop):
    """노션 속성에서 텍스트를 안전하게 꺼내는 헬퍼"""
    t = prop.get("type")
    if t == "title":
        return "".join(x["plain_text"] for x in prop["title"])
    if t == "rich_text":
        return "".join(x["plain_text"] for x in prop["rich_text"])
    if t == "select":
        return prop["select"]["name"] if prop["select"] else ""
    if t == "url":
        return prop.get("url") or ""
    return ""


def fetch_today_news():
    """노션 DB에서 '오늘 하루' 저장된 뉴스만 읽어온다"""
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1) DB에서 데이터소스 ID 찾기
    db = notion.databases.retrieve(database_id=DB_ID)
    data_source_id = db["data_sources"][0]["id"]

    # 2) 오늘 0시 이후 AND 내일 0시 이전 (= 오늘 하루)
    res = notion.data_sources.query(
        data_source_id=data_source_id,
        filter={
            "and": [
                {"property": "날짜", "date": {"on_or_after": today}},
                {"property": "날짜", "date": {"before": tomorrow}},
            ]
        },
    )

    items = []
    for page in res["results"]:
        p = page["properties"]
        items.append({
            "분류": get_text(p.get("분류", {})),
            "제목": get_text(p.get("제목", {})),
            "요약": get_text(p.get("요약", {})),
            "시사점": get_text(p.get("시사점", {})),
            "질문": get_text(p.get("질문", {})),
        })
    return items

def build_context(news):
    """뉴스들을 LLM에게 줄 맥락 텍스트로 조립"""
    lines = []
    for n in news:
        lines.append(
            f"[{n['분류']}] {n['제목']}\n"
            f"요약: {n['요약']}\n"
            f"시사점: {n['시사점']}\n"
            f"던진 질문: {n['질문']}\n"
        )
    return "\n".join(lines)


def main():
    print("오늘의 뉴스를 불러오는 중...\n")
    news = fetch_today_news()

    if not news:
        print("오늘 저장된 뉴스가 없어요. n8n 워크플로우를 먼저 실행했는지 확인해보세요.")
        return

    context = build_context(news)

    # 화면에 오늘 뉴스와 질문 보여주기
    for n in news:
        print(f"[{n['분류']}] {n['제목']}")
        print(f"  질문: {n['질문']}\n")

    print("=" * 50)
    print("위 질문에 대해 생각을 나눠봐요. (끝내려면 quit 입력)")
    print("=" * 50 + "\n")

    # 대화 기록 (시스템 프롬프트에 오늘 뉴스 맥락을 심음)
    messages = [{
        "role": "system",
        "content": (
            "너는 사용자가 오늘의 경제·IT 뉴스에 대해 스스로 생각을 정리하도록 "
            "돕는 대화 파트너야. 아래는 오늘 뉴스의 요약·시사점·질문이야. "
            "사용자의 답에 대해 판단을 강요하지 말고, 더 깊이 생각하도록 "
            "짧고 날카로운 반문이나 관점을 제시해줘.\n\n" + context
        ),
    }]

    while True:
        user = input("나: ").strip()
        if user.lower() in ("quit", "exit", "종료"):
            print("\n대화를 마칠게요. 수고했어요!")
            break
        if not user:
            continue

        messages.append({"role": "user", "content": user})
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        answer = resp.choices[0].message.content
        print(f"\nAI: {answer}\n")
        messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()