def build_pagination_urls(request, page_number, page_size, total_items):
    has_more_items = len(total_items) == page_size

    next_page_url = None
    previous_page_url = None

    if has_more_items:
        next_page_url = request.build_absolute_uri(
            f"{request.path}?page={page_number + 1}&page_size={page_size}"
        )

    if page_number > 1:
        previous_page_url = request.build_absolute_uri(
            f"{request.path}?page={page_number - 1}&page_size={page_size}"
        )

    return {
        "has_more_items": has_more_items,
        "next_page": next_page_url,
        "previous_page": previous_page_url,
    }
