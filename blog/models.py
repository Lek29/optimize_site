from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch


class PostQuerySet(models.QuerySet):
    def year(self, year):
        posts_at_year = self.filter(published_at__year=year).order_by('published_at')
        return posts_at_year

    def popular(self):
        return self.annotate(like_count=Count('likes', distinct=True)).order_by('-like_count')

    def fetch_with_comments_count(self):
        """
        Почему это лучше, чем обычный annotate:
        - Мы выполняем один запрос для всех постов, а не для каждого по отдельности.
        - Результат преобразуется в список, что удобно для использования в шаблонах.
        """
        # post_ids = self.values_list('id', flat=True)
        # post_with_comments = (
        #     Post.objects.filter(id__in=post_ids)
        #     .annotate(comments_count=Count('comments', distinct=True))
        # )
        # ids_and_comments = post_with_comments.values_list('id', 'comments_count')
        # count_for_id = dict(ids_and_comments)
        #
        # posts = list(self)
        # for post in posts:
        #     post.comments_count = count_for_id.get(post.id, 0)
        #
        # return posts
        # posts = Post.objects.filter(id__in=self).annotate(comments_count=Count('comments'))
        posts = self.annotate(comments_count=Count('comments', distinct=True))
        return posts

    def fresh(self):
        return self.order_by('-published_at')

class TagQuerySet(models.QuerySet):
    def popular(self):
        return self.annotate(posts_count=Count('posts')).order_by('-posts_count')[:5]

    def prefetch_with_post_count(self):
        return self.prefetch_related(
            Prefetch(
                'tags',
                queryset=Tag.objects.annotate(posts_count=Count('posts'),
                to_attr='annotated_tags',                         )
            )
        )


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации', db_index=True)
    objects = PostQuerySet.as_manager()

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)
    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'


