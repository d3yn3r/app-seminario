from django.db.models import Q


def if_and_only_if(a: Q, b: Q) -> Q:
    return a & b | ~a & ~b


def different(a: Q, b: Q) -> Q:
    return a & ~b | ~a & b
