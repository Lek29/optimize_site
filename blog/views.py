from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count, Prefetch


def serialize_tag_with_posts_count(tag):
    return {
        'title': tag.title,
        'posts_with_tag': getattr(tag, 'posts_count', 0)
    }


def get_related_posts_count(tag):
    return tag.posts.count()

def get_like_count(post):
    return post.like_count


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': len(Comment.objects.filter(post=post)),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def serialize_post_optimized(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag_with_posts_count(tag) for tag in getattr(post, 'annotated_tags', post.tags.all())],
        'first_tag_title': getattr(post, 'annotated_tags', post.tags.all())[0].title if post.tags.exists() else None,
    }


def index(request):
    most_popular_tags = Tag.objects.popular()

    most_popular_posts = (
        Post.objects.popular()
        .prefetch_related('author', 'tags')
        .fetch_with_comments_count()[:5]
    )

    most_fresh_posts = (
        Post.objects.fresh()
        .prefetch_related(
            Prefetch(
                'tags',
                queryset=Tag.objects.annotate(posts_count=Count('posts')),
                to_attr='annotated_tags'
            ),
            'author'
        )
        .annotate(comments_count=Count('comments', distinct=True))[:5]
    )


    context = {
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_optimized(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],

    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.get(slug=slug)

    comments = Comment.objects.filter(post=post).select_related('author')

    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    likes = post.likes.all()

    related_tags = post.tags.annotate(posts_count=Count('posts')).all()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': len(likes),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = Tag.objects.popular()


    popular_posts_with_likes = (
        Post.objects.annotate(like_count=Count('likes', distinct=True))
        .order_by('-like_count')[:5]
    )


    post_ids = [post.id for post in popular_posts_with_likes]
    posts_with_comments = (
        Post.objects.filter(id__in=post_ids)
        .annotate(comments_count=Count('comments', distinct=True))
    )

    comments_count_map = {post.id: post.comments_count for post in posts_with_comments}

    for post in popular_posts_with_likes:
        post.comments_count = comments_count_map.get(post.id, 0)


    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in popular_posts_with_likes
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    most_popular_tags = Tag.objects.popular()

    most_popular_posts = list(
        Post.objects
        .annotate(like_count=Count('likes'))
        .order_by('-like_count')[:5]
    )

    related_posts = tag.posts.annotate(comments_count=Count('comments')).all()[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})