from django.shortcuts import get_object_or_404
from django.db import models
from django.db.models import Count, Exists, Q, OuterRef, Value

from rest_framework import status, generics, permissions
from rest_framework.response import Response

from fm.mixins import MultipleFieldLookupMixin, ListHeaderMixin
from fm.models import User, Post, Friend, Comment, Tag, City

from fm.serializers import PostSerializer, UserDetailsSerializer, \
    ProfileSerializer, FriendSerializer, FriendListSerializer, \
    CommentSerializer, PostLikeSerializer, PostFollowSerializer, \
    TagSerializer, PostExtendedSerializer, NoteSerializer, \
    NoteBestSerializer, PostAttachSerializer, CitySerializer

from fm.permissions import IsOwnerOrReadOnly

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailsSerializer

class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailsSerializer
    lookup_url_kwarg = 'user'

class ProfileDetail(generics.RetrieveUpdateAPIView):
    """
    get: Возвращает параметры профиля пользователя.
    put: Редактирует параметры профиля пользователя.
    patch: Редактирует параметры профиля пользователя.
    """
    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    def get_object(self):
        obj = get_object_or_404(User.objects, email=self.request.user)
        return obj

class ProfileQuestions(generics.ListAPIView):
    """
    Возвращает список собственных вопросов пользователя.
    """
    serializer_class = PostSerializer

    def get_queryset(self):
        posts = Post.objects.filter(author=self.request.user,
            typeContent=Post.QUESTION).annotate(
            countLike=Count('likes', distinct=True),
            countComnt=Count('post_comments', distinct=True))
        return posts

class ProfileNotes(generics.ListAPIView):
    """
    Возвращает список собственных рекомендаций пользователя.
    """
    serializer_class = PostSerializer

    def get_queryset(self):
        posts = Post.objects.filter(author=self.request.user,
            typeContent__in=[Post.POSITIVE, Post.NEGATIVE]).annotate(
            countLike=Count('likes', distinct=True),
            countComnt=Count('post_comments', distinct=True))
        return posts

class ProfileFollows(generics.ListAPIView):
    """
    Возвращает список постов за которыми следит пользователь.
    """
    serializer_class = PostSerializer

    def get_queryset(self):
        user_likes = Post.likes.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        posts = Post.objects.filter(follows=self.request.user).annotate(
            countLike=Count('likes', distinct=True),
            isLike=Exists(user_likes),
            countComnt=Count('post_comments', distinct=True))
        return posts

class FriendList(generics.ListAPIView):
    """
    Возвращает список всех друзей пользователя.
    """
    serializer_class = FriendListSerializer

    def get_queryset(self):
        friend_follows = Friend.objects.filter(author=self.request.user, friend=OuterRef('pk'))
        friends = User.objects.exclude(pk=self.request.user.pk).exclude(is_staff=True) \
            .annotate(isFollow=Exists(friend_follows))
        return friends

class FriendFollow(generics.CreateAPIView, generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = FriendSerializer
    lookup_field = 'id'

    def perform_create(self, serializers):
        Friend.objects.update_or_create(
            author=self.request.user, friend=self.get_object(),
            defaults={'follow': True})

    def perform_destroy(self, instance):
        Friend.objects.filter(author=self.request.user, friend=instance) \
            .delete()

class PostList(generics.ListCreateAPIView):
    """
    get: Выводит список всех вопросов и рекомендаций.
    post: Создает новый вопрос или рекомендацию с указанными параметрами.
    """
    serializer_class = PostSerializer
    results_field = 'posts'

    def get_queryset(self):
        user_likes = Post.likes.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        user_follows = Post.follows.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        posts = Post.objects.annotate(
            countLike=Count('likes', distinct=True),
            isLike=Exists(user_likes),
            countComnt=Count('post_comments', distinct=True),
            isFollow=Exists(user_follows))

        post_type = self.request.query_params.getlist('type')
        post_type = list(filter(None, post_type))
        if post_type:
            # TODO: Сделать проверку вводимых данных
            posts = posts.filter(typeContent__in=post_type)

        search = self.request.query_params.get('search', None)
        if search:
            posts = posts.filter(Q(title__icontains=search) | Q(description__icontains=search))

        tags = self.request.query_params.getlist('tag')
        tags = list(filter(None, tags))
        if tags:
            posts = posts.filter(tags__tag__in=tags)

        # TODO: Не использовать JOIN здесь. Сначала получить список id городов по их именам,
        # а потом фильтровать по этому списку id.
        city = self.request.query_params.getlist('city')
        city = list(filter(None, city))
        if city:
            posts = posts.filter(city__name__in=city)

        return posts

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get(self, request, *args, **kwargs):
        # Добавляю все полученные посты в прочитанные
        posts = self.get_queryset()
        self.request.user.posts_viewed.add(*posts)

        return self.list(request, *args, **kwargs)

class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    get: Выводит указанный вопрос или рекомендацию.
    put: Редактирует указанный вопрос или рекомендацию.
    patch: Редактирует указанный вопрос или рекомендацию.
    delete: Удаляет указанный вопрос или рекомендацию.
    """
    serializer_class = PostSerializer
    lookup_url_kwarg = 'post'
    # permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def get_queryset(self):
        user_likes = Post.likes.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        user_follows = Post.follows.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        post = Post.objects.annotate(
            countLike=Count('likes', distinct=True),
            isLike=Exists(user_likes),
            countComnt=Count('post_comments', distinct=True),
            isFollow=Exists(user_follows))
        return post

class CommentList(generics.ListCreateAPIView):
    """
    get: Выводит список всех коментариев к указанной рекомендации.
    post: Создает новый комментарий к указанной рекомендации.
    """
    serializer_class = CommentSerializer

    def get_post(self):
        post = get_object_or_404(Post.objects, pk=self.kwargs['post'])
        return post

    def get_queryset(self):
        comment = Comment.objects.filter(post=self.get_post())
        return comment

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, post_id=self.get_post().pk)

class CommentDetail(MultipleFieldLookupMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    get: Выводит указанный комментарий к посту.
    put: Редактирует указанный комментарий к посту.
    patch: Редактирует указанный комментарий к посту.
    delete: Удаляет указанный комментарий к посту.
    """
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    lookup_fields = ('post', 'id')

class CommentReply(MultipleFieldLookupMixin, generics.CreateAPIView):
    """
    post: Создает новый комментарий в ответ на указанный комментарий.
    """
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def get_post(self):
        post = get_object_or_404(Post.objects, pk=self.kwargs['post'])
        return post

    def get_comment(self):
        comment = get_object_or_404(Comment.objects.filter(post=self.get_post()), pk=self.kwargs['id'])
        return comment

    def perform_create(self, serializer):
        # TODO: Удалить "parent"? Вроде не нужен если есть "reply_to".
        parent = self.get_comment()
        serializer.save(author=self.request.user, post_id=self.get_post().pk,
            parent=parent, reply_to=parent.author)

class PostLike(generics.CreateAPIView, generics.DestroyAPIView):
    """
    post: Ставит отметку "понравилось" (like) на указанный комментарий.
    delete: Снимает отметку "понравилось" (like) на указанный комментарий.
    """
    serializer_class = PostLikeSerializer
    queryset = Post.objects.all()
    lookup_url_kwarg = 'post'

    # TODO: Возвращать текущие значения.

    def perform_create(self, serializers):
        post = self.get_object()
        post.likes.add(self.request.user)

    def perform_destroy(self, instance):
        instance.likes.remove(self.request.user)

class PostFollow(generics.CreateAPIView, generics.DestroyAPIView):
    """
    post: Включет отслеживание указанного комментария.
    delete: Отключает отслеживание указанного комментария.
    """
    serializer_class = PostFollowSerializer
    queryset = Post.objects.all()
    lookup_url_kwarg = 'post'

    def perform_create(self, serializers):
        post = self.get_object()
        post.follows.add(self.request.user)

    def perform_destroy(self, instance):
        instance.follows.remove(self.request.user)

class TagList(generics.ListAPIView):
    """
    Выводит список всех имеющихся тэгов.
    """
    serializer_class = TagSerializer
    pagination_class = None
    queryset = Tag.objects.all()
    list_name = 'tags'

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        tags = [val['tag'] for val in serializer.data]
        return Response({self.list_name: tags})

class CityList(generics.ListAPIView):
    """
    Выводит список всех имеющихся городов.
    """
    serializer_class = CitySerializer
    pagination_class = None
    queryset = City.objects.all()
    list_name = 'cities'

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        cities = [val['name'] for val in serializer.data]
        return Response({self.list_name: cities})

class PostSimilar(generics.ListAPIView):
    """
    Выводит список всех похожих (по тэгам) вопросов и рекомендаций.
    """
    serializer_class = PostSerializer

    def get_queryset(self):
        # TODO: Возвращать 404 если нет такого поста
        post_id = self.kwargs['post']
        tags = Post.tags.through.objects.filter(post_id=post_id).values('tag_id')
        posts = Post.objects.filter(tags__in=tags).exclude(pk=post_id).distinct()
        return posts

class PostExtended(generics.RetrieveAPIView):
    """
    Выводит расширенную информацию об указанном вопросе или рекомендации:
    список похожих вопросов/рекомендаций, комментарии, рекомендации.
    """
    serializer_class = PostExtendedSerializer
    lookup_url_kwarg = 'post'

    def get_post(self):
        post = get_object_or_404(Post.objects, pk=self.kwargs['post'])
        return post

    def get_queryset(self):
        user_likes = Post.likes.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        user_follows = Post.follows.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        post = Post.objects.annotate(
            countLike=Count('likes', distinct=True),
            isLike=Exists(user_likes),
            countComnt=Count('post_comments', distinct=True),
            isFollow=Exists(user_follows))
        return post

    def get_serializer_context(self):
        context = super(PostExtended, self).get_serializer_context()
        context.update({
            "best_note": self.get_post().best_note
        })
        return context

class NoteList(generics.ListCreateAPIView):
    """
    get: Выводит список рекомендаций к указанному вопросу.
    post: Добавляет новую рекомендацию к указанному вопросу.
    """
    serializer_class = PostSerializer

    def get_post(self):
        if not 'post' in self.kwargs:
            return None
        post = get_object_or_404(Post.objects,
            pk=self.kwargs['post'], typeContent=Post.QUESTION)
        return post

    def get_queryset(self):
        post = self.get_post()
        user_likes = Post.likes.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        user_follows = Post.follows.through.objects.filter(
            post=OuterRef('pk'), user=self.request.user)
        notes = Post.objects.filter(note__post=post).annotate(
            countLike=Count('likes', distinct=True),
            isLike=Exists(user_likes),
            countComnt=Count('post_comments', distinct=True),
            isFollow=Exists(user_follows))
        return notes

        # TODO: Выдача коментариев с прикрепленными постами
        # comments = Comment.objects.filter(post=self.get_post())
        # return comments

    def perform_create(self, serializer):
        note = serializer.save(author=self.request.user)
        comment = Comment(author=self.request.user, post=self.get_post(),
            note=note)
        comment.save()

    def get_serializer_context(self):
        context = super(NoteList, self).get_serializer_context()
        post = self.get_post()
        if post is not None:
            context.update({"best_note": post.best_note})
        return context

class NoteDetail(generics.RetrieveUpdateAPIView):
    """
    get: Выводит указанную рекомендацию к вопросу.
    put: Редактирует указанную рекомендацию к вопросу.
    patch: Редактирует указанную рекомендацию к вопросу.
    """
    serializer_class = PostSerializer
    queryset = Comment.objects.all()

    def get_post(self):
        post = get_object_or_404(Post.objects,
            pk=self.kwargs['post'], typeContent=Post.QUESTION)
        return post

    def get_object(self):
        note = get_object_or_404(Post.objects,
            note__post=self.get_post(), note__note=self.kwargs['id'])
        return note

        # TODO: Выдача коментариев с прикрепленными постами
        # comment = get_object_or_404(Comment.objects,
        #     post=self.get_post(), pk=self.kwargs['id'])
        # return comment

class NoteBest(generics.CreateAPIView, generics.DestroyAPIView):
    """
    post: Устанавливает указанную рекомендацию как "лучшую" к данному вопросу.
    delete: Удаляет "лучшую" рекомендацию к данному вопросу.
    """
    serializer_class = NoteBestSerializer
    queryset = Post.objects.all()
    lookup_url_kwarg = 'post'

    # TODO: Возвращать текущие значения.

    def perform_create(self, serializer):
        post = self.get_object()
        post.best_note = get_object_or_404(Post.objects, pk=self.kwargs['id'])
        post.save()

    def perform_destroy(self, instance):
        instance.best_note = None
        instance.save()

class PostAttach(generics.CreateAPIView):
    """
    Добавляет рекомендацию к данному вопросу.
    """
    serializer_class = PostAttachSerializer

    def get_post(self):
        post = get_object_or_404(Post.objects,
            pk=self.kwargs['post'], typeContent=Post.QUESTION)
        return post

    def perform_create(self, serializer):
        notes = Post.objects.filter(
            pk__in=serializer.data['attach'],
            typeContent__in=[Post.POSITIVE, Post.NEGATIVE],
            author=self.request.user)
        for n in notes:
            Comment.objects.get_or_create(
                author=self.request.user, post=self.get_post(), note=n)
