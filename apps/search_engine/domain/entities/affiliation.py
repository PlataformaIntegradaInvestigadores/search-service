from django_neomodel import DjangoNode
from neomodel import StringProperty, UniqueIdProperty


class Affiliation(DjangoNode):
    scopus_id = UniqueIdProperty()
    name = StringProperty(unique_index=True)
    city = StringProperty()
    country = StringProperty()

    class Meta:
        app_label = "search_engine"

    @classmethod
    def from_dict(cls, affiliation_data):
        scopus_id = affiliation_data.get("afid")
        name = affiliation_data.get("affilname")
        city = affiliation_data.get("affiliation-city")
        country = affiliation_data.get("affiliation-country")
        try:
            affiliation_instance = cls.nodes.get_or_none(scopus_id=scopus_id)
            if affiliation_instance:
                return affiliation_instance

            affiliation_instance = cls.nodes.get_or_none(name=name)
            if affiliation_instance:
                affiliation_instance.scopus_id = scopus_id
                affiliation_instance.city = city
                affiliation_instance.country = country
                affiliation_instance.save()
                return affiliation_instance

            affiliation_instance = cls(
                scopus_id=scopus_id, name=name, city=city, country=country
            ).save()
            return affiliation_instance
        except Exception as e:
            raise Exception(f"Error while processing affiliation data: {str(e)}")

    @classmethod
    def retrieve_from_json(cls, affiliation_data):
        try:
            if not isinstance(affiliation_data, dict):
                return None

            scopus_id = affiliation_data.get("@affiliation-id")
            extra_information = affiliation_data.get("ip-doc", {})

            if not isinstance(extra_information, dict):
                return None

            address = extra_information.get("address", {})
            if not isinstance(address, dict):
                address = {}

            parent_name_data = extra_information.get("parent-preferred-name")
            preferred_name_data = extra_information.get("preferred-name")

            if parent_name_data is not None and not isinstance(parent_name_data, dict):
                parent_name_data = None
            if preferred_name_data is not None and not isinstance(
                preferred_name_data, dict
            ):
                preferred_name_data = None

            city = address.get("city")
            country = address.get("country")

            name = None

            if parent_name_data:
                name = parent_name_data.get("$")
            if not name and preferred_name_data:
                name = preferred_name_data.get("$")

            if not name:
                return None

            try:
                affiliation_instance = cls.nodes.get_or_none(scopus_id=scopus_id)
                if affiliation_instance:
                    return affiliation_instance

                affiliation_instance = cls.nodes.get_or_none(name=name)
                if affiliation_instance:
                    affiliation_instance.scopus_id = scopus_id
                    affiliation_instance.city = city
                    affiliation_instance.country = country
                    affiliation_instance.save()
                    return affiliation_instance

                affiliation_instance = cls(
                    scopus_id=scopus_id, name=name, city=city, country=country
                ).save()
                return affiliation_instance
            except Exception as e:
                raise Exception(f"Error while processing affiliation data: {str(e)}")

        except Exception as e:
            raise Exception(f"Error while retrieving affiliation from JSON: {str(e)}")
