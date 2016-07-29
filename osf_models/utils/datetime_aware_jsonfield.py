import json
from functools import partial

from django.contrib.postgres import lookups
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from psycopg2.extras import Json

from osf_models.exceptions import ValidationError

class DateTimeAwareJSONField(JSONField):
    def get_prep_value(self, value):
        if value is not None:
            return Json(value, dumps=partial(json.dumps, cls=DjangoJSONEncoder))
        return value


    def get_prep_lookup(self, lookup_type, value):
        if lookup_type in ('has_key', 'has_keys', 'has_any_keys'):
            return value
        if isinstance(value, (dict, list)):
            return Json(value, dumps=partial(json.dumps, cls=DjangoJSONEncoder))
        return super(JSONField, self).get_prep_lookup(lookup_type, value)

    def validate(self, value, model_instance):
        super(JSONField, self).validate(value, model_instance)
        try:
            json.dumps(value, cls=DjangoJSONEncoder)
        except TypeError:
            raise ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )


JSONField.register_lookup(lookups.DataContains)
JSONField.register_lookup(lookups.ContainedBy)
JSONField.register_lookup(lookups.HasKey)
JSONField.register_lookup(lookups.HasKeys)
JSONField.register_lookup(lookups.HasAnyKeys)
