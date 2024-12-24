from rest_framework import serializers
from .models import ChatSession, Message, Advertisement, Map, IssueCategory, Issue, Question, DiagnosticStep, Option, SubscriptionPlan, UserSubscription

class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ['id', 'title', 'image', 'category']



class IssueCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueCategory
        fields = '__all__'

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'



class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'





class DiagnosticStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticStep
        fields = '__all__'


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = '__all__'



# سریالایزر پلن‌ها
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    access_to_categories = IssueCategorySerializer(many=True, read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = "__all__"

# سریالایزر اشتراک کاربران
class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    active_categories = IssueCategorySerializer(many=True, read_only=True)

    class Meta:
        model = UserSubscription
        fields = ["plan", "active_categories", "start_date", "end_date", "is_active"]

    


class AdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertisement
        fields = ['id', 'title', 'link', 'banner', 'created_at']





class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'session', 'sender', 'content', 'timestamp']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'consultant', 'is_active', 'created_at', 'messages']