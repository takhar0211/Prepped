import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Question

questions = [
    {
        "title": "Design Twitter (System Design)",
        "slug": "design-twitter-system-design",
        "description": "<h3>Design Twitter</h3><p>Design a simplified version of Twitter where users can post tweets, follow/unfollow another user, and is able to see the 10 most recent tweets in the user's news feed.</p>",
        "difficulty": "Hard",
        "topic": "System Design",
        "starter_code": {}
    },
    {
        "title": "Design URL Shortener (System Design)",
        "slug": "design-url-shortener",
        "description": "<h3>Design a URL Shortener like TinyURL</h3><p>Design a service like TinyURL, a URL shortening service, a web service that provides short aliases for redirection of long URLs.</p>",
        "difficulty": "Medium",
        "topic": "System Design",
        "starter_code": {}
    },
    {
        "title": "Design a Web Crawler (System Design)",
        "slug": "design-web-crawler",
        "description": "<h3>Design a Web Crawler</h3><p>Design a distributed web crawler that will crawl all the pages on the internet, store them, and allow them to be searchable.</p>",
        "difficulty": "Hard",
        "topic": "System Design",
        "starter_code": {}
    },
    {
        "title": "Design WhatsApp / Chat Service (System Design)",
        "slug": "design-whatsapp",
        "description": "<h3>Design a Chat Service</h3><p>Design a chat messenger service like WhatsApp or Facebook Messenger. The system should support 1-on-1 chat, group chat, and indicate user online presence.</p>",
        "difficulty": "Hard",
        "topic": "System Design",
        "starter_code": {}
    },
    {
        "title": "Design a Key-Value Store (System Design)",
        "slug": "design-key-value-store",
        "description": "<h3>Design a Distributed Key-Value Store</h3><p>Design a highly available and scalable distributed key-value store. It should support Put(key, value) and Get(key) operations with high throughput.</p>",
        "difficulty": "Hard",
        "topic": "System Design",
        "starter_code": {}
    }
]

for q in questions:
    obj, created = Question.objects.get_or_create(
        slug=q['slug'],
        defaults=q
    )
    if created:
        print(f"Created System Design question: {q['title']}")
    else:
        print(f"Already exists: {q['title']}")
