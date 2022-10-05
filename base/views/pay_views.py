from django.shortcuts import redirect
from django.views.generic import View, TemplateView
from django.conf import settings
from stripe.api_resources import tax_rate
from base.models import Item, Order
import stripe
from django.contrib.auth.mixins import LoginRequiredMixin
# modelをjson形式に変換できる。
from django.core import serializers
import json
from django.contrib import messages
# メール送信用
from config import settings
from django.core.mail import send_mail


    
stripe.api_key = settings.STRIPE_API_SECRET_KEY
    
def make_sentence(shipping, items):
    shipping = json.loads(shipping)[0]['fields']
    shi_sentence = 'name:{}\nzipcode:{}\nprefecture:{}\ncity:{}\naddress1:{}\naddress2:{}\ntel:{}\n'.format(
        shipping['name'],
        shipping['zipcode'],
        shipping['prefecture'],
        shipping['city'],
        shipping['address1'],
        shipping['address2'],
        shipping['tel'],
    )
    # shi_sentence = [type(shipping), len(shipping)]
    item_sentence = []
    items = json.loads(items)
    for i in range(len(items)):
        # item_sentence = [type(items),len(items)]
        item_sentence.append('{}が{}個'.format(items[i]['name'], items[i]['quantity']))
    item_sentence = '\n'.join(item_sentence)

    return send_mail('発送準備通知', f'{shi_sentence}\n{item_sentence}', 'from@example.com',
            ['teardrop.reo0420@gmail.com'],fail_silently=False,
            )


class PaySuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/success.html'
    
    def get(self, request, *args, **kwargs):
        # 最新のOrderオブジェクトを取得し、注文確定に変更
        order = Order.objects.filter(
            user=request.user).order_by('-created_at')[0]
        order.is_confirmed = True
        order.save()
    
        # カート情報削除
        del request.session['cart']
        
        #メール送信
        make_sentence(order.shipping, order.items)
    
        return super().get(request, *args, **kwargs)
    
    
class PayCancelView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/cancel.html'
    
    def get(self, request, *args, **kwargs):
        # 最新のOrderオブジェクトを取得
        order = Order.objects.filter(
                user=request.user).order_by('-created_at')[0]
    
        # 在庫数と販売数を元の状態に戻す
        for x_item in json.loads(order.items):
            item = Item.objects.get(pk=x_item['pk'])
            item.sold_count -= x_item['quantity']
            item.stock += x_item['quantity']
            item.save()
    
        # is_confirmedがFalseであれば削除（仮オーダー削除）
        if not order.is_confirmed:
            order.delete()
    
        return super().get(request, *args, **kwargs)
    
    
tax_rate = stripe.TaxRate.create(
    display_name='消費税',
    description='消費税',
    country='JP',
    jurisdiction='JP',
    percentage=settings.TAX_RATE * 100,
    inclusive=False,  # 外税を指定（内税の場合はTrue）
)
    
    
def create_line_item(unit_amount, name, quantity):
    return {
        'price_data': {
            'currency': 'JPY',
            'unit_amount': unit_amount,
            'product_data': {'name': name, }
        },
        'quantity': quantity,
        'tax_rates': [tax_rate.id]
    }
    
    
def check_profile_filled(profile):
    if profile.name is None or profile.name == '':
        return False
    elif profile.zipcode is None or profile.zipcode == '':
        return False
    elif profile.prefecture is None or profile.prefecture == '':
        return False
    elif profile.city is None or profile.city == '':
        return False
    elif profile.address1 is None or profile.address1 == '':
        return False
    return True


class PayWithStripe(LoginRequiredMixin, View):
    
    def post(self, request, *args, **kwargs):
        # プロフィールが埋まっているかどうか確認
        if not check_profile_filled(request.user.profile):
            messages.error(request, '配送に必要なプロフィールを埋めてください。')
            return redirect('/profile/')
    
        cart = request.session.get('cart', None)
        if cart is None or len(cart) == 0:
            messages.error(request, 'カートが空です。')
            return redirect('/')

        items = [] # Orderモデル用
        line_items = []
        for item_pk, quantity in cart['items'].items():
            item = Item.objects.get(pk=item_pk)
            line_item = create_line_item(
                item.price, item.name, quantity)
            line_items.append(line_item)

            # Orderモデル用
            items.append({
                'pk': item.pk,
                'name': item.name,
                'image': str(item.image),
                'price': item.price,
                'quantity': quantity,
            })

            # 在庫をこの時点でも引いておく、注文のキャンセルの場合は在庫を戻す。
            # 販売数も加算しておく。
            item.stock -= quantity
            item.sold_count += quantity
            item.save()
    
        # 仮注文を作成
        Order.objects.create(
            user=request.user,
            uid=request.user.pk,
            items=json.dumps(items),
            shipping=serializers.serialize('json', [request.user.profile]),
            amount=cart['total'],
            tax_included=cart['tax_included_total']
        )

        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f'{settings.MY_URL}/pay/success/',
            cancel_url=f'{settings.MY_URL}/pay/cancel/',
        )
        return redirect(checkout_session.url)