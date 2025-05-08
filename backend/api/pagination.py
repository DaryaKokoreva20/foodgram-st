from rest_framework.pagination import PageNumberPagination

INGREDIENTS_PAGE_SIZE = 6


class IngredientPagination(PageNumberPagination):
    page_size = INGREDIENTS_PAGE_SIZE
    page_size_query_param = 'limit'
