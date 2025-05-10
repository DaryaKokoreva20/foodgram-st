from rest_framework.pagination import PageNumberPagination

from constants import (
    INGREDIENTS_PAGE_SIZE
)


class IngredientPagination(PageNumberPagination):
    page_size = INGREDIENTS_PAGE_SIZE
    page_size_query_param = 'limit'
