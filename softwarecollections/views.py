from django.views.generic.list import ListView
from .models import SoftwareCollection

class SCLsList(ListView):
    model = SoftwareCollection
    paginate_by = 10

