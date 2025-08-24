from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import CreateAPIView 
from rest_framework.permissions import AllowAny


from .models import Farm, Cow, MilkProduction, Activity, User, Enrollment
from .serializers import (
    FarmSerializer, CowSerializer, MilkProductionSerializer,
    ActivitySerializer, UserSerializer, EnrollmentSerializer, RegistrationSerializer
)
from .permissions import (
    IsSuperAdmin, IsAgent, IsFarmer,
    IsAdminOrAgent, IsFarmerOrAdmin,
    AuthenticatedOrReadOnly, PostAdminOrAgentElseAuth, PostFarmerOrAdminElseAuth
)

# Roles & Pagination
ADMIN, AGENT, FARMER = "admin", "agent", "farmer"

class MyPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

def _paginate(qs, request, Serializer):
    paginator = MyPagination()
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(Serializer(page, many=True).data)

# Helping
def _err(msg="Permission denied.", code=403):
    return Response({"detail": msg}, status=code)

def _is_admin(u):  return getattr(u, "role", None) == ADMIN
def _is_agent(u):  return getattr(u, "role", None) == AGENT
def _is_farmer(u): return getattr(u, "role", None) == FARMER

def _farms_managed(user):
    return Farm.objects.filter(agent=user)

def _active_farm_for_farmer(user):
    if not _is_farmer(user):
        return None
    e = (Enrollment.objects
         .filter(user=user, is_active=True)
         .select_related("farm")
         .order_by("-enrolled_at")
         .first())
    return e.farm if e else getattr(user, "farm", None)

def _agent_owns_farm(agent, farm):
    return farm.agent_id == agent.id

def _cow_access_ok(user, cow):
    return (
        _is_admin(user)
        or (_is_agent(user) and _agent_owns_farm(user, cow.farm))
        or (_is_farmer(user) and cow.farmer_id == user.id)
    )

def _record_access_ok(user, cow, recorder=None):
    if _is_admin(user):
        return True
    if _is_agent(user):
        return _agent_owns_farm(user, cow.farm)
    if _is_farmer(user):
        return recorder and recorder.id == user.id
    return False

# Users
@swagger_auto_schema(method="get", responses={200: UserSerializer(many=True)})
@api_view(["GET"])
@permission_classes([IsAuthenticated]) 
def user_list(request):
    u = request.user
    if _is_admin(u):
        users = User.objects.all()
    elif _is_agent(u):
        farms = _farms_managed(u)
        users = User.objects.filter(
            Q(id=u.id) | Q(role=FARMER, enrollments__farm__in=farms)
        ).distinct()
    elif _is_farmer(u):
        users = User.objects.filter(id=u.id)
    else:
        return _err()
    return _paginate(users.select_related(), request, UserSerializer)

@swagger_auto_schema(method="post", request_body=UserSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminOrAgent])  
def farmer_create(request):
    u = request.user
    farm_id = request.data.get("farm")
    if not farm_id:
        return Response({"farm": ["This field is required."]}, status=400)
    farm = get_object_or_404(Farm, id=farm_id)
    if _is_agent(u) and not _agent_owns_farm(u, farm):
        return _err("You can only assign farmers to your own farm(s).")

    ser = UserSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)
    farmer_user = ser.save(role=FARMER)
    Enrollment.objects.get_or_create(
        user=farmer_user, farm=farm, defaults={"is_active": True}
    )
    return Response(UserSerializer(farmer_user).data, status=201)

@swagger_auto_schema(method="post", request_body=UserSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def agent_create(request):
    ser = UserSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)
    agent_user = ser.save(role=AGENT)
    return Response(UserSerializer(agent_user).data, status=201)


# Farms
@swagger_auto_schema(method="get", responses={200: FarmSerializer(many=True)})
@swagger_auto_schema(method="post", request_body=FarmSerializer)
@api_view(["GET", "POST"])
@permission_classes([PostAdminOrAgentElseAuth])   
def farm_list_create(request):
    u = request.user

    if request.method == "GET":
        if _is_admin(u):
            farms = Farm.objects.all().select_related("agent")
        elif _is_agent(u):
            farms = _farms_managed(u).select_related("agent")
        elif _is_farmer(u):
            f = _active_farm_for_farmer(u)
            farms = Farm.objects.filter(id=f.id).select_related("agent") if f else Farm.objects.none()
        else:
            return _err()
        return _paginate(farms, request, FarmSerializer)

    ser = FarmSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)
    if _is_agent(u):
        farm = ser.save(agent=u)
    else: 
        agent_id = request.data.get("agent")
        if not agent_id:
            return Response(
                {"agent": ["This field is required (SuperAdmin must assign an Agent)."]},
                status=400,
            )
        agent_user = get_object_or_404(User, id=agent_id, role=AGENT)
        farm = ser.save(agent=agent_user)
    return Response(FarmSerializer(farm).data, status=201)

@swagger_auto_schema(method="get", responses={200: FarmSerializer})
@swagger_auto_schema(method="put", request_body=FarmSerializer)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AuthenticatedOrReadOnly]) 
def farm_detail(request, pk):
    u = request.user
    farm = get_object_or_404(Farm.objects.select_related("agent"), pk=pk)

    if request.method == "GET":
        if (_is_admin(u)
            or (_is_agent(u) and _agent_owns_farm(u, farm))
            or (_is_farmer(u) and _active_farm_for_farmer(u) and _active_farm_for_farmer(u).id == farm.id)):
            return Response(FarmSerializer(farm).data)
        return _err()

    if request.method == "PUT":
        if not (_is_admin(u) or (_is_agent(u) and _agent_owns_farm(u, farm))):
            return _err("Only the SuperAdmin or the farm's Agent can update this farm.")
        data = request.data.copy()
        if _is_agent(u):
            data.pop("agent", None)
        ser = FarmSerializer(farm, data=data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        if _is_admin(u) and data.get("agent"):
            new_agent = get_object_or_404(User, id=data["agent"], role=AGENT)
            updated = ser.save(agent=new_agent)
        else:
            updated = ser.save(agent=farm.agent)
        return Response(FarmSerializer(updated).data)

    if not (_is_admin(u) or (_is_agent(u) and _agent_owns_farm(u, farm))):
        return _err("Only the SuperAdmin or the farm's Agent can delete this farm.")
    farm.delete()
    return Response({"detail": "Farm deleted."}, status=204)

# Cows
@swagger_auto_schema(method="get", responses={200: CowSerializer(many=True)})
@swagger_auto_schema(method="post", request_body=CowSerializer)
@api_view(["GET", "POST"])
@permission_classes([AuthenticatedOrReadOnly]) 
def cow_list_create(request):
    u = request.user

    if request.method == "GET":
        if _is_farmer(u):
            cows = Cow.objects.filter(farmer=u).select_related("farm", "farmer")
        elif _is_agent(u):
            cows = Cow.objects.filter(farm__in=_farms_managed(u)).select_related("farm", "farmer")
        elif _is_admin(u):
            cows = Cow.objects.all().select_related("farm", "farmer")
        else:
            return _err()
        return _paginate(cows, request, CowSerializer)

    ser = CowSerializer(data=request.data)
    if _is_farmer(u):
        farm = _active_farm_for_farmer(u)
        if not farm:
            return _err("No active enrollment found for this farmer.", code=400)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        cow = ser.save(farmer=u, farm=farm)
        return Response(CowSerializer(cow).data, status=201)

    if _is_agent(u) or _is_admin(u):
        farmer_id = request.data.get("farmer")
        if not farmer_id:
            return Response({"farmer": ["This field is required."]}, status=400)
        farmer = get_object_or_404(User, id=farmer_id, role=FARMER)
        farm = _active_farm_for_farmer(farmer) or getattr(farmer, "farm", None)
        if not farm:
            return _err("Target farmer has no active farm/enrollment.", code=400)
        if _is_agent(u) and not _agent_owns_farm(u, farm):
            return _err("You can only add cows for farmers in your assigned farm(s).")
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        cow = ser.save(farmer=farmer, farm=farm)
        return Response(CowSerializer(cow).data, status=201)

    return _err()

@swagger_auto_schema(method="get", responses={200: CowSerializer})
@swagger_auto_schema(method="put", request_body=CowSerializer)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AuthenticatedOrReadOnly]) 
def cow_detail(request, pk):
    u = request.user
    cow = get_object_or_404(Cow.objects.select_related("farm", "farmer"), pk=pk)

    if request.method == "GET":
        return Response(CowSerializer(cow).data) if _cow_access_ok(u, cow) else _err()

    if request.method == "PUT":
        if not _cow_access_ok(u, cow):
            return _err("Only the owner (farmer), farm manager (agent), or SuperAdmin can update this cow.")
        data = request.data.copy()
        if not _is_admin(u):
            data.pop("farmer", None)
            data.pop("farm", None)
        ser = CowSerializer(cow, data=data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        if _is_admin(u) and ("farmer" in data or "farm" in data):
            new_farmer = cow.farmer
            new_farm = cow.farm
            if "farmer" in data:
                new_farmer = get_object_or_404(User, id=data["farmer"], role=FARMER)
                new_farm = _active_farm_for_farmer(new_farmer) or getattr(new_farmer, "farm", None) or new_farm
            if "farm" in data:
                new_farm = get_object_or_404(Farm, id=data["farm"])
            updated = ser.save(farmer=new_farmer, farm=new_farm)
        else:
            updated = ser.save(farmer=cow.farmer, farm=cow.farm)
        return Response(CowSerializer(updated).data)

    if not _cow_access_ok(u, cow):
        return _err("Only the owner (farmer), farm manager (agent), or SuperAdmin can delete this cow.")
    cow.delete()
    return Response({"detail": "Cow deleted."}, status=204)

# Milk Production
@swagger_auto_schema(method="get", responses={200: MilkProductionSerializer(many=True)})
@swagger_auto_schema(method="post", request_body=MilkProductionSerializer)
@api_view(["GET", "POST"])
@permission_classes([PostFarmerOrAdminElseAuth])   
def milkproduction_list_create(request):
    u = request.user

    if request.method == "GET":
        if _is_farmer(u):
            records = MilkProduction.objects.filter(recorded_by=u).select_related("cow", "cow__farmer", "cow__farm")
        elif _is_agent(u):
            records = (MilkProduction.objects
                       .filter(cow__farm__in=_farms_managed(u))
                       .select_related("cow", "cow__farmer", "cow__farm"))
        elif _is_admin(u):
            records = MilkProduction.objects.all().select_related("cow", "cow__farmer", "cow__farm")
        else:
            return _err()
        return _paginate(records, request, MilkProductionSerializer)

    ser = MilkProductionSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)
    record = ser.save(recorded_by=u if _is_farmer(u) else ser.validated_data.get("recorded_by", u))
    return Response(MilkProductionSerializer(record).data, status=201)

@swagger_auto_schema(method="get", responses={200: MilkProductionSerializer})
@swagger_auto_schema(method="put", request_body=MilkProductionSerializer)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AuthenticatedOrReadOnly]) 
def milkproduction_detail(request, pk):
    u = request.user
    rec = get_object_or_404(
        MilkProduction.objects.select_related("cow", "recorded_by", "cow__farm"),
        pk=pk
    )

    if request.method == "GET":
        return Response(MilkProductionSerializer(rec).data) if _record_access_ok(u, rec.cow, rec.recorded_by) else _err()

    if request.method == "PUT":
        if not (_is_admin(u) or (_is_farmer(u) and rec.recorded_by_id == u.id)):
            return _err("Only the original recording farmer or SuperAdmin can update this record.")
        data = request.data.copy()
        if _is_farmer(u):
            data.pop("recorded_by", None)
        ser = MilkProductionSerializer(rec, data=data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        updated = ser.save(recorded_by=rec.recorded_by)
        return Response(MilkProductionSerializer(updated).data)

    if not (_is_admin(u) or (_is_farmer(u) and rec.recorded_by_id == u.id)):
        return _err("Only the original recording farmer or SuperAdmin can delete this record.")
    rec.delete()
    return Response({"detail": "Milk production record deleted."}, status=204)

# Activities
@swagger_auto_schema(method="get", responses={200: ActivitySerializer(many=True)})
@swagger_auto_schema(method="post", request_body=ActivitySerializer)
@api_view(["GET", "POST"])
@permission_classes([PostFarmerOrAdminElseAuth])  
def activity_list_create(request):
    u = request.user

    if request.method == "GET":
        if _is_farmer(u):
            activities = Activity.objects.filter(recorded_by=u).select_related("cow", "cow__farm", "cow__farmer")
        elif _is_agent(u):
            activities = (Activity.objects
                          .filter(cow__farm__in=_farms_managed(u))
                          .select_related("cow", "cow__farm", "cow__farmer"))
        elif _is_admin(u):
            activities = Activity.objects.all().select_related("cow", "cow__farm", "cow__farmer")
        else:
            return _err()
        return _paginate(activities, request, ActivitySerializer)

    ser = ActivitySerializer(data=request.data, context={"request": request})
    ser.is_valid(raise_exception=True)
    activity = ser.save() 
    return Response(ActivitySerializer(activity, context={"request": request}).data, status=201)


@swagger_auto_schema(method="get", responses={200: ActivitySerializer})
@swagger_auto_schema(method="put", request_body=ActivitySerializer)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AuthenticatedOrReadOnly]) 
def activity_detail(request, pk):
    u = request.user
    act = get_object_or_404(Activity.objects.select_related("cow", "recorded_by", "cow__farm"), pk=pk)

    if request.method == "GET":
        return Response(ActivitySerializer(act).data) if _record_access_ok(u, act.cow, act.recorded_by) else _err()

    if request.method == "PUT":
        if not (_is_admin(u) or (_is_farmer(u) and act.recorded_by_id == u.id)):
            return _err("Only the original recording farmer or SuperAdmin can update this activity.")
        data = request.data.copy()
        if _is_farmer(u):
            data.pop("recorded_by", None)
        ser = ActivitySerializer(act, data=data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        updated = ser.save(recorded_by=act.recorded_by)
        return Response(ActivitySerializer(updated).data)

    if not (_is_admin(u) or (_is_farmer(u) and act.recorded_by_id == u.id)):
        return _err("Only the original recording farmer or SuperAdmin can delete this activity.")
    act.delete()
    return Response({"detail": "Activity record deleted."}, status=204)

# Enrollments
@swagger_auto_schema(method="get", responses={200: EnrollmentSerializer(many=True)})
@swagger_auto_schema(method="post", request_body=EnrollmentSerializer)
@api_view(["GET", "POST"])
@permission_classes([PostAdminOrAgentElseAuth])   
def enrollment_list_create(request):
    u = request.user

    if request.method == "GET":
        if _is_admin(u):
            enrollments = Enrollment.objects.select_related("user", "farm", "farm__agent")
        elif _is_agent(u):
            enrollments = Enrollment.objects.select_related("user", "farm").filter(farm__agent=u)
        elif _is_farmer(u):
            enrollments = Enrollment.objects.select_related("user", "farm").filter(user=u)
        else:
            return _err()
        return _paginate(enrollments, request, EnrollmentSerializer)

    ser = EnrollmentSerializer(data=request.data, context={"request": request})
    ser.is_valid(raise_exception=True)  

    farm = ser.validated_data.get("farm")
    user_obj = ser.validated_data.get("user")

    if _is_agent(u) and farm.agent_id != u.id:
        return _err("You can only enroll farmers into your own farm(s).", code=403)

    enrollment = ser.save()
    return Response(EnrollmentSerializer(enrollment, context={"request": request}).data, status=201)


@swagger_auto_schema(method="get", responses={200: EnrollmentSerializer})
@swagger_auto_schema(method="put", request_body=EnrollmentSerializer)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AuthenticatedOrReadOnly])   
def enrollment_detail(request, pk):
    u = request.user
    enr = get_object_or_404(Enrollment.objects.select_related("user", "farm", "farm__agent"), pk=pk)

    if request.method == "GET":
        can_view = (
            _is_admin(u)
            or (_is_agent(u) and _agent_owns_farm(u, enr.farm))
            or (_is_farmer(u) and enr.user_id == u.id)
        )
        return Response(EnrollmentSerializer(enr).data) if can_view else _err()

    if request.method == "PUT":
        can_update = _is_admin(u) or (_is_agent(u) and _agent_owns_farm(u, enr.farm))
        if not can_update:
            return _err()
        data = request.data.copy()
        if _is_agent(u):
            data.pop("user", None)
            data.pop("farm", None)
        ser = EnrollmentSerializer(enr, data=data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        updated = ser.save() if _is_admin(u) else ser.save(user=enr.user, farm=enr.farm)
        return Response(EnrollmentSerializer(updated).data)

    can_delete = _is_admin(u) or (_is_agent(u) and _agent_owns_farm(u, enr.farm))
    if not can_delete:
        return _err()
    if _is_agent(u):
        enr.is_active = False
        enr.save(update_fields=["is_active"])
        return Response({"detail": "Enrollment deactivated."}, status=200)
    enr.delete()
    return Response({"detail": "Enrollment deleted."}, status=204)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh token is required"}, status=400)
        try:
            token = RefreshToken(refresh)
            token.blacklist() 
        except Exception:
            return Response({"detail": "invalid refresh token"}, status=400)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class RegisterView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer
    @swagger_auto_schema(request_body=RegistrationSerializer)  
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get(self, request, format=None):
        content = {
            'status': 'request was permitted'
        }
        return Response(content)
