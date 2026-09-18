from rest_framework import serializers


class LoggerRequestSerializer(serializers.Serializer):
    lines_per_page = serializers.IntegerField(required=False, default=10)
    page = serializers.IntegerField(required=False, default=1)
    level = serializers.CharField(required=False, default="INFO")
    start_date = serializers.CharField(required=False, default="")
    end_date = serializers.CharField(required=False, default="")
    keyword = serializers.CharField(required=False, default="")
