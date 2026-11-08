from django.urls import path

from .views import (
    PostListCreateView,
    PostDetailView,
    PostUpdateDeleteView,
    ToggleBookmarkView,
    ToggleLikeView,
    CommentCreateView,
    SharePostView,
    PostCommentListView,
    CommentUpdateDeleteView,
    CommentDetailView,
)


urlpatterns = [

    # POSTS

    path(
        "",
        PostListCreateView.as_view(),
        name="post-list"
    ),

    path(
        "<int:pk>/",
        PostDetailView.as_view(),
        name="post-detail"
    ),

    path(
        "<int:pk>/manage/",
        PostUpdateDeleteView.as_view(),
        name="post-manage"
    ),


    # LIKES

    path(
        "<int:pk>/like/",
        ToggleLikeView.as_view(),
        name="post-like"
    ),


    # BOOKMARKS

    path(
        "<int:pk>/bookmark/",
        ToggleBookmarkView.as_view(),
        name="post-bookmark"
    ),


    # SHARES

    path(
        "<int:pk>/share/",
        SharePostView.as_view(),
        name="post-share"
    ),


    # COMMENTS

    path(
        "<int:pk>/comment/",
        CommentCreateView.as_view(),
        name="post-comment"
    ),

    path(
        "<int:pk>/comments/",
        PostCommentListView.as_view(),
        name="post-comments"
    ),

    path(
        "comments/<int:pk>/",
        CommentDetailView.as_view(),
        name="comment-detail"
    ),

    path(
        "comments/<int:pk>/manage/",
        CommentUpdateDeleteView.as_view(),
        name="comment-manage"
    ),
]