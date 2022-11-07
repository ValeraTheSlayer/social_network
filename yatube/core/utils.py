from django.core.paginator import Paginator


def paginate(request, queryset, pagesize):
    return Paginator(queryset, pagesize).get_page(request.GET.get('page'))


def truncatechars(chars: str, trim: int):
    return chars[:trim] + '…' if len(chars) > trim else chars
