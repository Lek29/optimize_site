from django.shortcuts import render, get_object_or_404
from blog.models import Comment, Post, Tag
from django.db.models import Count, Prefetch
import logging



logger = logging.getLogger(__name__)
def serialize_tag(tag):
    logger.debug(f"Serializing tag: {tag.title}, posts_count: {getattr(tag, 'posts_count', 'N/A')}")
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in getattr(post, 'annotated_tags', [])], #
        'first_tag_title': getattr(post, 'annotated_tags', [])[0].title if getattr(post, 'annotated_tags', []) else None,
    }


def index(request):
    most_popular_tags = Tag.objects.popular()

    most_popular_posts = (
        Post.objects.popular()
        .select_related('author')
        .prefetch_related('tags')
        .fetch_with_comments_count()[:5]
    )

    most_fresh_posts = (
        Post.objects.fresh()
        .select_related('author')
        .prefetch_related(Tag.objects.prefetch_with_post_count())
        .annotate(comments_count=Count('comments', distinct=False))[:5]
    )

    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)

def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related('author').get(slug=slug))

    comments = Comment.objects.filter(post=post).select_related('author')

    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    related_tags = post.tags.annotate(posts_count=Count('posts')).all()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes.count(),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = Tag.objects.annotate(posts_count=Count('posts')).popular()

    popular_posts_with_likes = (
        Post.objects.annotate(like_count=Count('likes', distinct=False))
        .order_by('-like_count')[:5]
    )

    post_ids = [post.id for post in popular_posts_with_likes]
    posts_with_comments = (
        Post.objects.filter(id__in=post_ids)
        .annotate(comments_count=Count('comments', distinct=False))
    )

    comments_count_map = {post.id: post.comments_count for post in posts_with_comments}
    for post in popular_posts_with_likes:
        post.comments_count = comments_count_map.get(post.id, 0)

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in popular_posts_with_likes
        ],
    }
    return render(request, 'post-details.html', context)

def tag_filter(request, tag_title):
    tag = Tag.objects.annotate(posts_count=Count('posts')).filter(title=tag_title).first()

    if tag is None:
        logger.error(f"Tag with title '{tag_title}' not found.")
        return render(request, '404.html', {})

    logger.debug(f"Tag: {tag.title}, Posts count: {getattr(tag, 'posts_count', 'N/A')}")

    most_popular_tags = Tag.objects.popular()
    most_popular_posts_with_likes = (
        Post.objects.annotate(like_count=Count('likes', distinct=False))
        .order_by('-like_count')[:5]
    )
    post_ids = [post.id for post in most_popular_posts_with_likes]
    posts_with_comments = (
        Post.objects.filter(id__in=post_ids)
        .annotate(comments_count=Count('comments', distinct=False))
    )
    comments_count_map = {post.id: post.comments_count for post in posts_with_comments}

    for post in most_popular_posts_with_likes:
        post.comments_count = comments_count_map.get(post.id, 0)

    related_posts = (
        tag.posts
        .select_related('author')
        .prefetch_related(
            Prefetch(
                'tags',
                queryset=Tag.objects.annotate(posts_count=Count('posts')),
                to_attr='annotated_tags'
            )
        )
        .annotate(comments_count=Count('comments')).all()[:20]
    )

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts_with_likes
        ],
    }
    return render(request, 'posts-list.html', context)

def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})