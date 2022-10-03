from django.views.generic import ListView, DetailView
from base.models import Order
import json
# loginしていなければページを見せないようにできる。
from django.contrib.auth.mixins import LoginRequiredMixin

class OrderIndexView(LoginRequiredMixin, ListView):
    model = Order   
    template_name = 'pages/orders.html'
    # 並び替えを降順にしている。（新しいのが上になる）
    ordering = '-created_at'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'pages/order.html'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # pkも決まっている1つのobjectを取ってきている。(詳細ページなので1つに決まっている。)
        obj = self.get_object()
        # json to dict
        context['items'] = json.loads(obj.items)
        context['shipping'] = json.loads(obj.shipping)
        return context
