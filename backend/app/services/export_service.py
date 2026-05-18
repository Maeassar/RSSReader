from app.repositories import repository


def article_markdown(article_id):
    article = repository.get_article(article_id)
    note = repository.get_note(article_id)
    return "\n\n".join(
        [
            f"# {article['title']}",
            f"Source: {article['url']}",
            article.get("cleaned_markdown") or article.get("summary") or "",
            "## Notes",
            note["content_markdown"],
        ]
    )


def articles_markdown(article_ids):
    return "\n\n---\n\n".join(article_markdown(article_id) for article_id in article_ids)

