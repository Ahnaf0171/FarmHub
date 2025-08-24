# farmhub/core/urls.py
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Users
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("users/", views.user_list, name="user-list"),
    path("users/farmers/", views.farmer_create, name="farmer-create"),
    path("users/agents/", views.agent_create, name="agent-create"),

    # Farms
    path("farms/", views.farm_list_create, name="farm-list-create"),
    path("farms/<int:pk>/", views.farm_detail, name="farm-detail"),

    # Cows
    path("cows/", views.cow_list_create, name="cow-list-create"),
    path("cows/<int:pk>/", views.cow_detail, name="cow-detail"),

    # Milk Production
    path("milk/", views.milkproduction_list_create, name="milkproduction-list-create"),
    path("milk/<int:pk>/", views.milkproduction_detail, name="milkproduction-detail"),

    # Activities
    path("activities/", views.activity_list_create, name="activity-list-create"),
    path("activities/<int:pk>/", views.activity_detail, name="activity-detail"),

    # Enrollments
    path("enrollments/", views.enrollment_list_create, name="enrollment-list-create"),
    path("enrollments/<int:pk>/", views.enrollment_detail, name="enrollment-detail"),
    
]
