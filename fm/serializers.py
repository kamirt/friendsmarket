from django.conf import settings
from django.core.mail import send_mail
from rest_framework import serializers
from fm.models import User, Post, Friend, Comment, Tag, City

class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """
    Вспомогательный slug сериализатор с возможностью создания элементов
    """
    def to_internal_value(self, data):
        obj, _ = self.get_queryset().get_or_create(**{self.slug_field: data})
        return obj

class NameSerializer(serializers.CharField):
    def to_representation(self, obj):
        return obj.get_full_name()

    def to_internal_value(self, data):
        names = data.split(maxsplit=1)
        ret = {
            "first_name": names[0] if len(names) > 0 else '',
            "last_name" : names[1] if len(names) > 1 else ''
        }
        return ret


class UserDetailsSerializer(serializers.ModelSerializer):
    name = NameSerializer(source='*', required=False)

    class Meta:
        model = User
        fields = ('id', 'name', 'gender', 'email', 'profile_photo', 'enable_notif')
        read_only_fields = ('email', )

class ProfileSerializer(serializers.ModelSerializer):
    name = NameSerializer(source='*', required=False)

    class Meta:
        model = User
        exclude = ('password', 'is_superuser', 'is_staff', 'is_active', 'groups', 'user_permissions')
        read_only_fields = ('email', 'username', 'created', 'last_login')
        extra_kwargs = {
            'android_regid': {'write_only': True}
        }

class FriendListSerializer(serializers.ModelSerializer):
    name = NameSerializer(source='*')
    isFollow = serializers.BooleanField()

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'isFollow')
        read_only_fields = ('id', 'email')

class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id',)

class AuthorSerializer(serializers.ModelSerializer):
    name = NameSerializer(source='*')

    class Meta:
        model = User
        fields = ('name', 'profile_photo')

class PostSerializer(serializers.ModelSerializer):
    isMy = serializers.SerializerMethodField()
    countLike = serializers.IntegerField(read_only=True)
    isLike = serializers.BooleanField(read_only=True)
    countComnt = serializers.IntegerField(read_only=True)
    isFollow = serializers.BooleanField(read_only=True)
    isBest = serializers.SerializerMethodField()
    tags = CreatableSlugRelatedField(many=True, required=False,
        queryset=Tag.objects.all(), slug_field='tag')
    city = CreatableSlugRelatedField(many=False, required=False,
        queryset=City.objects.all(), slug_field='name')
    author = AuthorSerializer(read_only=True)

    def get_isMy(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return obj.author == user

    def get_isBest(self, obj):
        best_note = self.context.get("best_note")
        return not best_note is None and best_note == obj

    class Meta:
        model = Post
        fields = ('id', 'typeContent', 'title', 'description', 'image',
            'created', 'isMy', 'countLike', 'isLike', 'countComnt',
            'isFollow', 'isBest', 'tags', 'city', 'author')
        read_only_fields = ('id', 'created')

class CommentSerializer(serializers.ModelSerializer):
    isMy = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    reply_to = AuthorSerializer(read_only=True)

    def get_isMy(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return obj.author == user

    class Meta:
        model = Comment
        fields = ('id', 'created', 'author', 'isMy', 'parent', 'reply_to', 'comment')
        read_only_fields = ('id', 'created', 'parent')

class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', )

class PostFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', )

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('tag', )

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('name', )

class PostExtendedSerializer(PostSerializer):
    comments = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    countSimilar = serializers.SerializerMethodField()
    similar = serializers.SerializerMethodField()

    def get_comments(self, obj):
        if obj.typeContent == Post.QUESTION:
            return None
        comments = obj.post_comments.all()[0:3]
        serializer = CommentSerializer(comments, 
            context=self.context, many=True, read_only=True)
        return serializer.data

    def get_notes(self, obj):
        if obj.typeContent in [Post.POSITIVE, Post.NEGATIVE]:
            return None
        posts = Post.objects.filter(note__post=obj)[0:3]
        serializer = PostSerializer(posts,
            context=self.context, many=True, read_only=True)
        return serializer.data

    def get_similar(self, obj):
        tags = obj.tags.all()
        posts = Post.objects.filter(tags__in=tags).exclude(pk=obj.pk).distinct()[0:3]
        serializer = PostSerializer(posts,
            context=self.context, many=True, read_only=True)
        return serializer.data

    def get_countSimilar(self, obj):
        tags = obj.tags.all()
        num = Post.objects.filter(tags__in=tags).exclude(pk=obj.pk).distinct().count()
        return num

    class Meta:
        model = Post
        fields = ('id', 'typeContent', 'title', 'description', 'image',
            'created', 'isMy', 'countLike', 'isLike', 'countComnt',
            'isFollow', 'isBest', 'tags', 'author', 'comments', 'notes',
            'countSimilar', 'similar')
        read_only_fields = ('id', 'created')

class NoteSerializer(serializers.ModelSerializer):
    note = PostSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'note')

class NoteBestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', )

class PostAttachSerializer(serializers.ModelSerializer):
    attach = serializers.ListField(allow_empty=False, child=serializers.IntegerField())

    class Meta:
        model = Post
        fields = ('attach', )

class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Нет пользователя с таким email")
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        password = User.objects.make_random_password()
        user.set_password(password)
        user.save()

        subject = 'Восстановление пароля'
        message = 'Здравствуйте, {0}!\n\nВаш новый пароль: {1}\n\n--\n\nС уважением,\nВаш Friendmarket'. \
            format(user.get_full_name(), password)

        email_from = getattr(settings, 'DEFAULT_FROM_EMAIL')

        send_mail(subject, message, email_from, [user.email], fail_silently=True)
