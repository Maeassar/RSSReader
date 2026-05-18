from fastapi import UploadFile


async def import_opml(file: UploadFile):
    content = await file.read()
    return {"ok": True, "message": f"OPML 文件已接收：{file.filename}，大小 {len(content)} bytes。当前为 Mock 导入。"}


def export_opml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>RSSReader Subscriptions</title></head>
  <body>
    <outline text="Open Source Weekly" title="Open Source Weekly" type="rss" xmlUrl="https://example.com/open-source.xml"/>
    <outline text="AI Research Digest" title="AI Research Digest" type="rss" xmlUrl="https://example.com/ai.xml"/>
  </body>
</opml>
"""

