from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 2  
    page_size_query_param = 'page_size'    
    page_query_param = 'page'  
    def get_paginated_response(self, data):
        return Response({
            'total_count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': len(data),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })