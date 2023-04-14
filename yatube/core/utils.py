from django.core.paginator import Paginator


def page_division(queryset, request, num):
    """Разбивает посты на страницы."""
    paginator = Paginator(queryset, num)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_obj': page_obj,
    }
