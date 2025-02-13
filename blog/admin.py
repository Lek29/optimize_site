from django.contrib import admin
from blog.models import Post, Tag, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'published_at', 'comments_count']
    raw_id_fields = ['author', 'tags']
    exclude = ('likes',)

    def comments_count(self, obj):
        return obj.comments.count()

    comments_count.short_description = 'Комментарии'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['text', 'post', 'author', 'published_at']
    raw_id_fields = ['post', 'author']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['title', 'posts_count']

    def posts_count(self, obj):
        return obj.posts.count()

    posts_count.short_description = 'Посты'


