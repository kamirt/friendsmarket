from django.contrib import admin
from django.forms import TextInput, Textarea, BaseForm
from django.db import models
from django.utils.safestring import mark_safe
from .models import Post, Comment, Tag, City, User
from rangefilter.filter import DateRangeFilter
from django.templatetags.static import StaticNode

class DateRangeFilterFM(DateRangeFilter):

   def get_template(self):
       return 'rangefilter/date_filter.html'

   template = property(get_template)

   def get_form(self, request):
       form_class = self._get_form_class()
       print(self.used_parameters)
       return form_class(self.used_parameters)

   def queryset(self, request, queryset):
       if self.form.is_valid():
           validated_data = dict(self.form.cleaned_data.items())
           print(validated_data)
           if validated_data.get('my_posts__created__gte'):
               queryset = queryset.filter(
                   my_posts__created__gte=validated_data.get('my_posts__created__gte') or date(1970, 1, 1),
                   my_posts__created__lte=validated_data.get('my_posts__created__lte') or date.today(),
                   )

           return queryset.annotate(created_count=models.Count('my_posts')) \
           .annotate(viewed_count=models.Count('posts_viewed'))
       return queryset

   @staticmethod
   def get_js():
       return [
          StaticNode.handle_simple('js/calendar.js'),
          StaticNode.handle_simple('js/DateTimeShortcuts.js'),
       ]

admin.site.site_header = 'Администрирование Friendmarket'
#admin.site.site_title =
from django.utils import timezone
from datetime import timedelta
from datetime import date

from django.contrib import admin

class CommentInline(admin.TabularInline):
    model = Comment
    fk_name = 'post'
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': TextInput(attrs={'size': 30})}
    }

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'typeContent', 'title', 'author_full_name', 'author', 'created', 'city')
    list_display_links = ('title', )
    list_filter = ('typeContent', 'city')

    fieldsets = (
        (None, {
            'fields': ('author', ('title', 'typeContent'), 'description', 'tags', 'city')
        }),
        ('Изображение', {
            'fields': ('image_preview', 'image')
        }),
        ('Дополнительно', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('best_note', ('likes', 'follows', 'viewed'))
        })
    )
    readonly_fields = ('image_preview', )
    radio_fields = {'typeContent': admin.HORIZONTAL}
    search_fields = ('title', )

    empty_value_display = '-нет-'

    inlines = (CommentInline, )

    def author_full_name(self, obj):
        return obj.author.get_full_name()
    author_full_name.short_description = 'Имя автора'

    def image_preview(self, obj):
        return mark_safe('<img src="{url}" width="{width}" height={height} />'.format(
                url=obj.image.url,
                width=obj.image.width,
                height=obj.image.height,
            )
        )
    image_preview.short_description = 'Изображение'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'post', 'author')
    list_display_links = ('comment', )

    fieldsets = (
        (None, {
            'fields': ('author', 'post', 'comment', 'note', ('parent', 'reply_to'))
        }),
    )
    search_fields = ('comment', 'post__title')

    empty_value_display = '-нет-'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag')
    list_display_links = ('id', )
    list_editable = ('tag', )
    ordering = ('tag', )

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', )
    list_editable = ('name', )
    ordering = ('name', )

class PostInline(admin.TabularInline):
    model = Post
    fk_name = 'author'
    extra = 0

    fields = ('typeContent', 'title', 'description', 'image')
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 5, 'cols': 50})}
    }

@admin.register(User)
class StatisticsAdmin(admin.ModelAdmin):
    
    def created_count(self, obj):
        return obj.created_count or ''

    created_count.short_description = 'Написано постов'

    def viewed_count(self, obj):
        return obj.viewed_count or ''

    viewed_count.short_description = 'Просмотрено постов'

    list_filter = (
        ('my_posts__created', DateRangeFilterFM),
    )

    list_display = ('username', 'email', 'last_login', 'created_count', 'viewed_count')
    list_display_links = ('email', )

    readonly_fields = ('created_count', 'viewed_count')
    fieldsets = (
        (None, {
            'fields': (('username', 'gender', 'email'), 'last_login', ('created_count', 'viewed_count'))
        }),
        ('Дополнительно', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('phone', 'birthday', 'profile_photo', 'enable_notif')
        }),
    )

    inlines = (PostInline, )

    # date_hierarchy = 'my_posts__created'
