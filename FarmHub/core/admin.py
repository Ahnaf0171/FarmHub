from django.contrib import admin
from .models import User, Farm, Cow, Activity, MilkProduction, Enrollment

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'mobile_no', 'is_active')
    search_fields = ['username', 'role', 'mobile_no']
    list_filter = ('role', 'is_active')
    list_editable = ('is_active',)

admin.site.register(User, UserAdmin)

class FarmAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'agent', 'is_active', 'farm_type', 'farm_size')
    search_fields = ['name', 'location', 'agent__username']
    list_filter = ('is_active', 'farm_type')
    list_editable = ('is_active', 'farm_type', 'farm_size')
    inlines = []

admin.site.register(Farm, FarmAdmin)

class CowAdmin(admin.ModelAdmin):
    list_display = ('tag_number', 'breed', 'farm', 'farmer', 'health_status', 'is_active')
    search_fields = ['tag_number', 'breed', 'farm__name', 'farmer__username']
    list_filter = ('health_status', 'is_active')
    list_editable = ('health_status', 'is_active')

admin.site.register(Cow, CowAdmin)

class ActivityAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'cow', 'recorded_by', 'date', 'category')
    search_fields = ['activity_type', 'cow__tag_number', 'recorded_by__username']
    list_filter = ('activity_type', 'category', 'date')
    list_editable = ('category',)

admin.site.register(Activity, ActivityAdmin)

class MilkProductionAdmin(admin.ModelAdmin):
    list_display = ('cow', 'quantity', 'date', 'recorded_by')
    search_fields = ['cow__tag_number', 'recorded_by__username']
    list_filter = ('date',)
    list_editable = ('quantity',)

admin.site.register(MilkProduction, MilkProductionAdmin)

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'farm', 'is_active', 'progress', 'is_completed', 'total_yield')
    search_fields = ['user__username', 'farm__name']
    list_filter = ('is_active', 'is_completed')
    list_editable = ('is_active', 'progress', 'is_completed', 'total_yield')

admin.site.register(Enrollment, EnrollmentAdmin)

admin.site.site_header = "FarmHub Administration"
admin.site.site_title = "FarmHub Admin"
admin.site.index_title = "Welcome to the FarmHub Admin Panel"
