from django.conf import settings
from django.core.paginator import Paginator


def paginate(request, queryset, pagesize: int = settings.PAGE_SIZE):
    return Paginator(queryset, pagesize).get_page(request.GET.get('page'))


def truncatechars(chars: str, trim: int = settings.TRUNCATE_CHARS):
    return chars[:trim] + '...' if len(chars) > trim else chars
