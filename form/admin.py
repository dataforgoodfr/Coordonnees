from django.contrib import admin
from dynamic_models.models import FieldSchema, ModelSchema


class FieldAdmin(admin.ModelAdmin):
    list_display = ["model_schema", "name"]


class SchemaAdmin(admin.ModelAdmin):
    list_display = ["name", "details"]

    def details(self, obj):
        return [
            f"{field.class_name.split('.')[-1]}:{field.name}"
            for field in obj.fields.all()
        ]


admin.site.register(FieldSchema, FieldAdmin)
admin.site.register(ModelSchema, SchemaAdmin)
