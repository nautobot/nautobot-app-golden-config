import re

from django.urls import path
from django.apps import apps
from django.utils.module_loading import import_string


def _verify_import_string(class_path):
    try:
        import_string(class_path)
    except ImportError:
        return False
    return True


def class_factory(class_name):
    class LocalClass(import_string(f"nautobot.core.views.generic.{class_name}")):
        pass

    return LocalClass


def generate_view(app_label, model_name):
    paths = []

    # Setup all of the different methods that are required
    lc_model_name = model_name.lower()
    route = re.sub(r"(?<!^)(?=[A-Z])", "-", model_name).lower()

    app_config = apps.get_app_config(app_label)
    model = app_config.get_model(model_name)
    model_queryset = model.objects.all()

    # For now, these are hard coded, but can easily follow the same pattern
    model_table = import_string(f"{app_label}.tables.{model_name}Table")
    model_filterset = import_string(f"{app_label}.filters.{model_name}Filter")
    model_filterset_form = import_string(f"{app_label}.forms.{model_name}FeatureFilterForm")
    model_form = import_string(f"{app_label}.forms.{model_name}Form")

    # This allows the ability to use "inheritance" of sorts, look for a more detailed one, and use that first.
    if _verify_import_string(f"{app_label}.views.{model_name}ListView"):
        list_view = import_string(f"{app_label}.views.{model_name}ListView")
    else:
        list_view = class_factory("ObjectListView")
    # Only override methods that don't exists yet
    if not list_view.queryset:
        list_view.queryset = model_queryset
    if not list_view.table:
        list_view.table = model_table
    if not list_view.filterset:
        list_view.filterset = model_filterset
    if not list_view.filterset_form:
        list_view.filterset_form = model_filterset_form
    # append to paths
    paths.append(path(f"{route}/", list_view.as_view(), name=f"{lc_model_name}_list"))

    # Simple one (meaning, no "inheritance" check), to prove that this should scale to more than one view type
    obj_view = class_factory("ObjectEditView")
    obj_view.queryset = model_queryset
    obj_view.model_form = model_form
    paths.append(path(f"{route}/add/", obj_view.as_view(), name=f"{lc_model_name}_add"))
    return paths
