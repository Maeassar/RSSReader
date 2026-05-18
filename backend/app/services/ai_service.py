from app.repositories import repository


def summarize(article_id):
    article = repository.get_article(article_id)
    result = f"模拟摘要：{article['title']} 主要说明了 RSSReader 的本地优先、内容清洗和可扩展接口设计。"
    return repository.create_ai_result(article_id, "summary", "Summarize article", result)


def translate(article_id):
    article = repository.get_article(article_id)
    result = f"Mock translation: {article['title']} explains the design of a local-first RSS reader."
    return repository.create_ai_result(article_id, "translation", "Translate article", result)


def suggest_tags(article_id):
    repository.get_article(article_id)
    result = "课程项目, AI, 工程实践"
    return repository.create_ai_result(article_id, "tag_suggestion", "Suggest tags", result)

