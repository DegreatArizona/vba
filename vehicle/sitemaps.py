# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
# from .models import Article  # Replace with your model

# class ArticleSitemap(Sitemap):
#     changefreq = "daily"
#     priority = 0.8

#     def items(self):
#         return Article.objects.all()

#     def lastmod(self, obj):
#         return obj.updated_at  # Ensure this field is in your model

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['index', 'login', 'register']  # Static views

    def location(self, item):
        return reverse(item)
