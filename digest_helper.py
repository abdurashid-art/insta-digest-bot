import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"

TONE_CONTEXT = (
    "Instagram-блог про путь студента к профессии врача-стоматолога (@future.dentt). "
    "Аудитория: абитуриенты и студенты-медики. Тон: живой, честный, без канцелярита, "
    "по-русски. Цели: охваты, конверсия в подписку, монетизация."
)


def build_account_update_text(profile, top_clips, prev_snapshot):
    """Чисто по фактам, без LLM — чтобы цифры были гарантированно реальными."""
    followers = profile.get("follower_count")
    media = profile.get("media_count")
    lines = [
        "<b>📊 Апдейт по твоему аккаунту</b>",
        f"@{profile.get('username')} — {followers} подписчиков, {media} постов",
    ]
    if prev_snapshot:
        delta_f = followers - prev_snapshot["follower_count"]
        sign = "+" if delta_f >= 0 else ""
        lines.append(f"С прошлого дайджеста: {sign}{delta_f} подписчиков")

    if top_clips:
        best = top_clips[0]
        lines.append(
            f"\nЛучший ролик сейчас: {best['play_count']} просмотров, "
            f"{best['like_count']} лайков"
        )
        cap = (best["caption"] or "").strip().split("\n")[0][:120]
        if cap:
            lines.append(f"«{cap}»")
    return "\n".join(lines)


SPLIT_MARKER = "===SCENARIOS==="


def generate_trend_breakdown_and_scenarios(trend_items, limit=5):
    """LLM используется ТОЛЬКО для качественного разбора и сценариев —
    все цифры, юзернеймы и подписи передаются как готовые реальные факты,
    LLM их не выдумывает, а только описывает содержание/формат/применение.

    Возвращает (breakdown_text, scenarios_text) — уже разделённые для двух
    отдельных сообщений в Telegram."""
    items = trend_items[:limit]
    facts = "\n".join(
        f"{i+1}. @{it['username']}: {it['play_count']} просмотров, найден по запросу «{it['query']}», "
        f"подпись целиком: {(it['caption'] or '(без подписи)')[:250]}"
        for i, it in enumerate(items)
    )

    prompt = f"""Вот реальные вирусные Reels (300 000 - 10 000 000 просмотров), найденные через
HikerAPI сегодня по разным нишам (не только медицина/стоматология — специально ищем
широко, чтобы находить рабочие форматы отовсюду):

{facts}

Контекст блога, для которого пишем: {TONE_CONTEXT}

Задача — для КАЖДОГО ролика из списка выше (используй только реальные данные из списка,
ничего не выдумывай про цифры/авторов):
1. В 1-2 предложениях опиши, о чём ролик и что в нём происходит — опирайся на подпись
   и тему запроса, по которой он нашёлся.
2. Назови формат (например: сторитайм, лайфхак, day in my life, POV, до/после,
   юмор/мем, образовательный контент, честная личная история и т.п.)
3. Дай ОДНУ конкретную идею, как этот формат применить в блоге про путь студента
   к профессии стоматолога — не общими словами, а прямо "сними X про Y".

Формат вывода для каждого ролика:
<b>[просмотры] @автор — формат</b>
о чём ролик (1-2 предложения)
💡 как применить: конкретная идея

После разбора ВСЕХ роликов выше — на новой строке ровно текст {SPLIT_MARKER}, а затем
напиши 2 готовых сценария Reels для @future.dentt, вдохновлённых этими трендами
(адаптируй под тему стоматологии/студенчества, не копируй темы дословно).
Для каждого: Хук (первая фраза на камеру), 3-4 пункта раскадровки, текст подписи
с призывом к действию.

Пиши по-русски, живо, без канцелярита. Не пиши вступлений и общих заключений, сразу
по делу. Ответ должен быть в HTML-разметке Telegram (разрешены только теги <b>, <i>,
без markdown, без ###)."""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000,
    )
    text = resp.choices[0].message.content.strip()

    if SPLIT_MARKER in text:
        breakdown, scenarios = text.split(SPLIT_MARKER, 1)
    else:
        breakdown, scenarios = text, ""

    breakdown_text = "<b>🔥 Свежие вирусные Reels — разбор</b>\n\n" + breakdown.strip()
    scenarios_text = "<b>🎬 Сценарии под свежие тренды</b>\n\n" + scenarios.strip() if scenarios.strip() else ""
    return breakdown_text, scenarios_text
