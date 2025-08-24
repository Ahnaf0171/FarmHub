from rest_framework import serializers
from .models import User, Farm, Cow, Activity, MilkProduction, Enrollment
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'mobile_no', 'password']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    role = serializers.ChoiceField(
        choices=User._meta.get_field("role").choices,
        default="farmer"
    )

    class Meta:
        model = User
        fields = (
            "id", "username","email", "first_name",
            "last_name", "mobile_no", "role",
            "password", "password2",
        )

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match."})

        if attrs.get("role") == "admin":
            raise serializers.ValidationError({"role": "Admin cannot self-register."})

        allow_agent = getattr(settings, "ALLOW_AGENT_SELF_SIGNUP", True)
        req = self.context.get("request")

        if attrs.get("role") == "agent" and not allow_agent:
            is_admin_request = bool(req and getattr(req.user, "is_staff", False))
            if not is_admin_request:
                raise serializers.ValidationError({"role": "Agent signup is disabled. Admin only."})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2", None)

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class FarmSerializer(serializers.ModelSerializer):
    agent = UserSerializer(read_only=True)

    class Meta:
        model = Farm
        fields = '__all__'

class CowSerializer(serializers.ModelSerializer):
    farm = FarmSerializer(read_only=True)
    farmer = UserSerializer(read_only=True)

    class Meta:
        model = Cow
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    cow = serializers.PrimaryKeyRelatedField(
        queryset=Cow.objects.all(), write_only=True
    )
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Activity
        fields = "__all__"

    def create(self, validated_data):
        validated_data["recorded_by"] = self.context["request"].user
        return super().create(validated_data)

class MilkProductionSerializer(serializers.ModelSerializer):
    cow = serializers.PrimaryKeyRelatedField(queryset=Cow.objects.all())
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MilkProduction
        fields = '__all__'

    def validate(self, attrs):
        request = self.context.get("request")
        cow = attrs.get("cow") or getattr(self.instance, "cow", None)
        if request and getattr(request.user, "role", "") == "farmer":
            if cow and cow.farmer_id != request.user.id:
                raise serializers.ValidationError(
                    "You can only record milk for your own cows."
                )
        return attrs

ADMIN, AGENT, FARMER = "admin", "agent", "farmer"
class EnrollmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=FARMER)
    )
    farm = serializers.PrimaryKeyRelatedField(
        queryset=Farm.objects.all()
    )

    class Meta:
        model = Enrollment
        fields = "__all__"  

    def _user(self):
        req = self.context.get("request")
        return getattr(req, "user", None)

    def validate(self, attrs):
        req_user = self._user()
        if not req_user or not getattr(req_user, "is_authenticated", False):
            raise serializers.ValidationError("Authentication required.")

        farm = attrs.get("farm")
        user = attrs.get("user")

        if user.role != FARMER:
            raise serializers.ValidationError({"user": "Only FARMER users can be enrolled."})

        if getattr(req_user, "role", None) == AGENT:
            if farm.agent_id != req_user.id:
                raise serializers.ValidationError("You can only enroll farmers into your own farm(s).")

        return attrs
    
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        if not value:
            raise serializers.ValidationError("Refresh token is required.")
        return value