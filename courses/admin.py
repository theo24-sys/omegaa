from django.contrib import admin
from .models import Course, CourseCompletion, Question, Choice, Lesson

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 3

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'is_free', 'is_mandatory', 'is_native')
    list_filter = ('is_free', 'is_mandatory', 'is_native')
    search_fields = ('title', 'description')
    inlines = [LessonInline, QuestionInline]
    ordering = ('-is_mandatory', 'price')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'course', 'order')
    list_filter = ('course',)
    inlines = [ChoiceInline]

@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'completed_at', 'has_certificate')
    list_filter = ('course', 'completed_at')
    search_fields = ('user__username', 'course__title')
    readonly_fields = ('completed_at',)

    def has_certificate(self, obj):
        return bool(obj.certificate)
    has_certificate.boolean = True
