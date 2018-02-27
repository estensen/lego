from django_filters.rest_framework import CharFilter, FilterSet, BooleanFilter

from lego.apps.companies.models import Semester
from .models import CompanyInterest


class SemesterFilterSet(FilterSet):
    company_interest = BooleanFilter('active_interest_form')

    class Meta:
        model = Semester
        fields = ('company_interest', )


class CompanyInterestFilterSet(FilterSet):
    company_name = CharFilter(lookup_expr='icontains')
    contact_person = CharFilter(lookup_expr='icontains')

    class Meta:
        model = CompanyInterest
        fields = ('company_name', 'contact_person')