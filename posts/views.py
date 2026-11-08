import re

from config.uploads import validate_images

from django.shortcuts import get_object_or_404

from posts.pagination import PostPagination
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
    JSONParser
)
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from .models import (
    Post,
    Like,
    Comment,
    PostImage,
    Share,
    Hashtag,
    Bookmark
)

from .serializers import (
    PostSerializer,
    CommentSerializer,
)

class PostListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = PostSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]

    pagination_class = PostPagination

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "content",
        "author__username",
        "hashtags__name",
    ]

    ordering_fields = [
        "created_at",
        "views_count",
        "likes_count",
    ]

    ordering = [
        "-created_at"
    ]


    def get_queryset(self):

        queryset = (
            Post.objects
            .select_related("author")
            .prefetch_related(
                "images",
                "hashtags",
            )
            .all()
        )

        hashtag = self.request.query_params.get(
            "hashtag"
        )

        if hashtag:

            hashtag = hashtag.lstrip("#")

            queryset = queryset.filter(
                hashtags__name__iexact=hashtag
            )

        return queryset.distinct()


    def perform_create(
        self,
        serializer
    ):

        validate_images(
            self.request.FILES.getlist("images")
        )

        post = serializer.save(
            author=self.request.user
        )

        # ======================
        # HASHTAGS
        # ======================

        hashtags = re.findall(
            r"#(\w+)",
            post.content
        )

        for tag in hashtags:

            hashtag, created = (
                Hashtag.objects.get_or_create(
                    name=tag.lower()
                )
            )

            post.hashtags.add(
                hashtag
            )

        # ======================
        # IMAGES
        # ======================

        images = self.request.FILES.getlist(
            "images"
        )

        for image in images:

            PostImage.objects.create(
                post=post,
                image=image
            )

from django.db.models import F
class PostDetailView(
    generics.RetrieveAPIView
):

    serializer_class = PostSerializer

    queryset = Post.objects.all()

    def retrieve(
        self,
        request,
        *args,
        **kwargs
    ):

        post = self.get_object()

        Post.objects.filter(
            pk=post.pk
        ).update(
            views_count=F("views_count") + 1
        )

        post.refresh_from_db()

        serializer = self.get_serializer(
            post
        )

        return Response(
            serializer.data
        )

class ToggleLikeView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        pk
    ):

        post = get_object_or_404(
            Post,
            pk=pk
        )

        like = Like.objects.filter(
            user=request.user,
            post=post
        )

        liked = False

        if like.exists():

            like.delete()

        else:

            Like.objects.create(
                user=request.user,
                post=post
            )

            liked = True

        post.refresh_from_db()

        return Response(
            {
                "liked": liked,
                "likes": post.likes_count,
            }
        )


class CommentCreateView(
    generics.CreateAPIView
):

    serializer_class = CommentSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def perform_create(
        self,
        serializer
    ):

        post = get_object_or_404(
            Post,
            pk=self.kwargs["pk"]
        )

        serializer.save(
            author=self.request.user,
            post=post
        )

class SharePostView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        pk
    ):

        post = get_object_or_404(
            Post,
            pk=pk
        )

        Share.objects.create(
            original_post=post,
            user=request.user,
            comment=request.data.get(
                "comment",
                ""
            )
        )

        post.refresh_from_db()

        return Response(
            {
                "message": "Post partagé avec succès",
                "shares": post.shares_count
            }
        )

class PostUpdateDeleteView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = Post.objects.all()

    serializer_class = PostSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return Post.objects.filter(
            author=self.request.user
        )


class ToggleBookmarkView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        pk
    ):

        post = get_object_or_404(
            Post,
            pk=pk
        )

        bookmark = Bookmark.objects.filter(
            user=request.user,
            post=post
        )

        bookmarked = False

        if bookmark.exists():

            bookmark.delete()

        else:

            Bookmark.objects.create(
                user=request.user,
                post=post
            )

            bookmarked = True

        post.refresh_from_db()

        return Response(
            {
                "bookmarked": bookmarked,
                "bookmarks": post.bookmarks_count
            }
        )

class PostCommentListView(
    generics.ListAPIView
):

    serializer_class = CommentSerializer

    def get_queryset(self):

        post = get_object_or_404(
            Post,
            pk=self.kwargs["pk"]
        )

        return Comment.objects.filter(
            post=post
        ).select_related(
            "author"
        )

class CommentDetailView(
    generics.RetrieveAPIView
):

    queryset = Comment.objects.select_related(
        "author",
        "post"
    )

    serializer_class = CommentSerializer

from .permissions import (
    IsCommentOwner
)

class CommentUpdateDeleteView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = Comment.objects.all()

    serializer_class = CommentSerializer

    permission_classes = [
        IsAuthenticated,
        IsCommentOwner
    ]