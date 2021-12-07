from django_jinja import library


@library.filter
def return_a(x):
    return "a"
