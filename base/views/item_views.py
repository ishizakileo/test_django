from django.shortcuts import render
from django.views.generic import ListView, DetailView
from base.models import Item, Category, Tag


class IndexListView(ListView):
	model = Item
	template_name = 'pages/index.html'
	# is_publishedで公開しているアイテムのみに絞る。
	queryset = Item.objects.filter(is_published=True)

## 上記のclassを関数で書いた場合。（classで書く場合は、継承するクラスの内部を知っている必要がある。）
# def index(request):
# 	object_list = Item.objects.all()
# 	context = {
# 	'object_list': object_list,
# 	}
# 	return render(request, 'pages/index.html', context)


class ItemdetailView(DetailView):
	model = Item
	template_name = 'pages/item.html'


class CategoryListView(ListView):
	model = Item
	template_name = 'pages/list.html'
	# 1ページに表示するアイテム数。
	paginate_by = 2

	# 関数を上書き
	def get_queryset(self):
		self.category = Category.objects.get(slug=self.kwargs['pk'])
		return Item.objects.filter(is_published=True, category=self.category)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['title'] = f'Category #{self.category.name}'
		return context


class TagListView(ListView):
	model = Item
	template_name = 'pages/list.html'
	paginate_by = 2

	def get_queryset(self):
		self.tag = Tag.objects.get(slug=self.kwargs['pk'])
		return Item.objects.filter(is_published=True, tags=self.tag)

	def get_context_data(self, **kwargs):
		# 一度親を呼び出して、titleを追加している。
		context = super().get_context_data(**kwargs)
		context['title'] = f'Tag #{self.tag.name}'
		return context

