from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_jwt.views import refresh_jwt_token
from fm import views

urlpatterns = [
    path('', include('rest_auth.urls')),
    path('registration/', include('rest_auth.registration.urls')),
    path('refresh-token/', refresh_jwt_token),

    path('profile/', views.ProfileDetail.as_view(), name='profile-view-update'),
    path('profile/questions/', views.ProfileQuestions.as_view(), name='profile-questions'),
    path('profile/notes/', views.ProfileNotes.as_view(), name='profile-notes'),
    path('profile/follows/', views.ProfileFollows.as_view(), name='profile-follows'),
    path('feed/', views.PostList.as_view(), name='feed-list'),
    path('friends/', views.FriendList.as_view(), name='friends-list'),
    path('friends/<int:id>/follow/', views.FriendFollow.as_view(), name='friends-follow'),

    path('users/', views.UserList.as_view(), name='users-list'),
    path('users/<int:user>/', views.UserDetail.as_view(), name='users-detail'),
    # path('users/<int:user>/friend/', views.UserFriend.as_view()),

    path('posts/', views.PostList.as_view(), name='posts-list'),
    path('posts/<int:post>/', views.PostDetail.as_view(), name='posts-detail'),
    path('posts/<int:post>/extended/', views.PostExtended.as_view(), name='posts-extended'),
    path('posts/<int:post>/attach/', views.PostAttach.as_view(), name='posts-attach'),
    path('posts/<int:post>/notes/', views.NoteList.as_view(), name='posts-notes-list'),
    path('posts/<int:post>/notes/<int:id>/', views.NoteDetail.as_view(), name='posts-notes-detail'),
    path('posts/<int:post>/notes/<int:id>/best/', views.NoteBest.as_view(), name='posts-notes-best'),
    path('posts/<int:post>/comments/', views.CommentList.as_view(), name='posts-comments-list'),
    path('posts/<int:post>/comments/<int:id>/', views.CommentDetail.as_view(), name='posts-comments-detail'),
    path('posts/<int:post>/comments/<int:id>/reply/', views.CommentReply.as_view(), name='posts-comments-reply'),
    path('posts/<int:post>/like/', views.PostLike.as_view(), name='posts-like'),
    path('posts/<int:post>/follow/', views.PostFollow.as_view(), name='posts-follow'),
    path('posts/<int:post>/similar/', views.PostSimilar.as_view(), name='posts-similar'),

    path('tags/', views.TagList.as_view(), name='tags-list'),

    path('cities/', views.CityList.as_view(), name='cities-list'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
