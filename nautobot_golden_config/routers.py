import re
from nautobot.core.views import generic
from django.urls import path
from django.apps import apps
import importlib



def class_factory(class_name):
    class LocalClass(getattr(importlib.import_module(f"nautobot_golden_config.routers"), class_name)):
        pass
    return LocalClass


def generate_view(app_label, model_name):
    paths = []

    # Setup all of the different methods that are required
    lc_model_name = model_name.lower()
    route = re.sub(r'(?<!^)(?=[A-Z])', '-', model_name).lower()

    app_config = apps.get_app_config(app_label)
    model = app_config.get_model(model_name)
    model_queryset = model.objects.all()

    # For now, these are hard coded, but can easily follow the same pattern
    model_table = getattr(importlib.import_module(f"{app_label}.tables"), f"{model_name}Table")
    model_filterset = getattr(importlib.import_module(f"{app_label}.filters"), f"{model_name}Filter")
    model_filterset_form = getattr(importlib.import_module(f"{app_label}.forms"), f"{model_name}FeatureFilterForm")
    model_form = getattr(importlib.import_module(f"{app_label}.forms"), f"{model_name}Form")

    # This allows the ability to use "inheritance" of sorts, look for a more detailed one, and use that first. 
    if hasattr(importlib.import_module(f"{app_label}.views"), f"{model_name}ListView"):
        list_view = getattr(importlib.import_module(f"{app_label}.views"), f"{model_name}ListView")
    else:
        list_view = class_factory("RouterListView")
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
    obj_view = class_factory("RouterEditView")
    obj_view.queryset = model_queryset
    obj_view.model_form = model_form
    paths.append(path(f"{route}/add/", obj_view.as_view(), name=f"{lc_model_name}_add"))
    return paths


class RouterListView(generic.ObjectListView):
    """View for displaying the current Line Replacements."""

class RouterView(generic.ObjectView):
    """View for single ConfigReplace instance."""

class RouterEditView(generic.ObjectEditView):
    """View for editing the current Line Replacements."""

class RouterBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting Line Replacements."""


class RouterBulkImportView(generic.BulkImportView):
    """View for bulk import of ConfigReplace."""

class RouterDeleteView(generic.ObjectDeleteView):
    """View for deleting a ConfigReplace instance."""


class RouterBulkEditView(generic.BulkEditView):
    """View for bulk deleting ConfigReplace instances."""
