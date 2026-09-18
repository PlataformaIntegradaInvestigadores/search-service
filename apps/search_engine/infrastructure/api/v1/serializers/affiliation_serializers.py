from rest_framework import serializers


class AffiliationSerializer(serializers.Serializer):
    scopus_id = serializers.CharField()
    name = serializers.CharField()
    city = serializers.CharField()
    country = serializers.CharField()


class AffiliationNameSerializer(serializers.Serializer):
    scopus_id = serializers.CharField()
    name = serializers.CharField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["scopusId"] = ret.pop("scopus_id")
        return ret

    def to_internal_value(self, data):
        data["scopus_id"] = data.pop("scopusId", None)
        return super().to_internal_value(data)
