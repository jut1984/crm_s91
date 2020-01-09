from django.conf.urls import url
from django.http import JsonResponse
from django.shortcuts import HttpResponse, render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q
from utils.mypage import Page
from utils.page import Pagination
from django.db.models.fields.related import ManyToManyField, ForeignKey
# 视图展示类
class ShowList(object):
    def __init__(self, config, data_list, request, list_display):
        self.config = config
        self.data_list = data_list
        self.request = request
        self.list_display = list_display
        self.actions = self.config.actions
        # 分页
        total_count = self.data_list.count()
        page_num = int(self.request.GET.get("page", 1))
        path = self.request.path
        self.page_obj = Pagination(page_num, total_count,  path, self.request.GET, pager_count=7, per_page_num=5)
        self.datalist = self.data_list[self.page_obj.start:self.page_obj.end]
        self.actions = self.config.new_actions()

    def get_filter_linktags(self):
        link_list = {}
        import copy

        for filter_field in self.config.list_filter:  # ['price', 'title', 'publish']

            # 深拷贝请求的参数信息
            params = copy.deepcopy(self.request.GET)
            if "page" in params:
                del params["page"]
            # print("idc", self.request.GET.get(filter_field))
            cid = self.request.GET.get(filter_field, 0)
            # 根据字符串获得当前表中的数据对象
            filter_field_obj = self.config.model._meta.get_field(filter_field)
            # 判断出入的对象是一对一或者一对多类型，进行关联查询，用rel.to.objects
            if isinstance(filter_field_obj, ManyToManyField)or isinstance(filter_field_obj, ForeignKey):
                data_list = filter_field_obj.rel.to.objects.all()
            else:  # 查询当前表内记录数据信息。[{'pk': 3, 'title': '123'}, {'pk': 4, 'title': '请问'}]
                data_list = self.config.model.objects.values('pk', filter_field)
            temp = []
            # 处理全部标签
            if params.get(filter_field):
                del params[filter_field]
                temp.append(f"<a href='?{params.urlencode()}'>全部</a>")
            else:
                temp.append(f"<a class='active' href='#'>全部</a>")

            # 处理数据标签
            for obj in data_list:
                # 如果是关联对象，则pk值需要关联查询，展示信息则直接obj.__str__转字符串
                if isinstance(filter_field_obj, ManyToManyField)or isinstance(filter_field_obj, ForeignKey):
                    pk = obj.pk
                    text = str(obj)
                    params[filter_field] = pk
                else:  # 是表内数据，直接get（"pk"）,展示信息直接获得对象信息值
                    pk = obj.get("pk")
                    text = obj.get(filter_field)
                    params[filter_field] = text
                # 把数据信息写入request的参数中：params中。

                # 给对应的参数进行序列化为authors=1&publish=2
                _url = params.urlencode()
                if str(pk) == cid or text == cid:
                    link_tag = f"<a class='active' href='?{_url}'>{text}</a>"
                else:
                    link_tag = f"<a href='?{_url}'>{text}</a>"
                temp.append(link_tag)
            link_list[filter_field] = temp
        return link_list


    def get_action_list(self):
        temp = []
        for action in self.actions:
            temp.append({
                "name": action.__name__,  # 把方法方法的名称传给模板
                "desc": action.short_description
            })
        return temp

    def get_header_list(self):
        header_list = []
        for field in self.config.new_list_play():  # ["id", "name", edit, delete]
            if isinstance(field, str):
                if field == "__str__":
                    val = self.config.model._meta.model_name.upper()
                else:
                    field_obj = self.config.model._meta.get_field(field)
                    val = field_obj.verbose_name
            else:
                val = field(self.config, is_header=True)
            header_list.append(val)
        return header_list

    def get_data(self):
        # 表单数据
        new_data = []
        for obj in self.datalist:
            tmp = []
            for field in self.config.new_list_play():  # ["__str__"]、["id", "name", edit]
                if callable(field):  # 检查对象是否可以被调用
                    print("----------",field)
                    val = field(self.config, obj)
                else:
                    try:
                        field_obj = self.config.model._meta.get_field(field)
                        if isinstance(field_obj, ManyToManyField):
                            ret = getattr(obj, field).all()
                            t = []
                            for i in ret:
                                t.append(str(i))
                            val = ','.join(t)
                        else:
                            if field_obj.choices:  # 获取modles表中有设置choices属性的对象，进行处理。
                                val= getattr(obj, "get_"+field+"_display")
                            else:
                                val = getattr(obj, field)
                            if field in self.config.list_display_links:
                                _url = self.config.get_change_url(obj)
                                val = mark_safe(f"<a href='{_url}'>{val}</>")
                    except Exception as e:
                        # 如果是__str__的时候会有报错。
                        val = getattr(obj, field)

                tmp.append(val)
            new_data.append(tmp)
        return new_data

# 配置类 每个表需要展示不同样式不同配置自定义
class ModelXadmin(object):
    list_display = ['__str__',]
    list_display_links = []
    list_filter = []
    modelform_class = []
    search_fields = []
    actions = []
    def path_delete(self, request, queryset):
        queryset.delete()

    path_delete.short_description = "批量删除"

    def __init__(self, model, site):
        self.model = model
        self.site = site

# print(new_data) = [
# [1, '好SQL必要', Decimal('23.98'), datetime.date(2019/9/24), <Publish: 牛哥出版社>],
# [2, '写SQL要3', Decimal('33.00'), datetime.date(2019/9/1), <Publish: 沙河出版社>]]
#     def edit(self, obj=None, is_header=False):
#         # 反向解析:url
#         if is_header:
#             return "操作"
#         _url = self.get_change_url(obj)
#         return mark_safe(f"<a href='{_url}'>编辑</a>")
#
#     def dele(self, obj=None, is_header=False):
#         if is_header:
#             return "操作"
#         pk = obj.pk
#         return mark_safe(f"<a id='a_del' data-toggle='modal' data-target='#id_del' obj_id='{pk}'>删除</a>")
#     操作栏添加新字段的对象数字，需要CRM子类继承重写方法。
    def operation_list(self, obj):
        return []

    def operation(self, obj=None, is_header=False):
        t = []
        if is_header:
            return "操作"
        print(obj)
        _url = self.get_change_url(obj)
        edit_p = f"<a href='{_url}'>编辑&nbsp;</a>"
        pk = obj.pk
        dele_p = f"<a id='a_del' data-toggle='modal' data-target='#id_del' obj_id='{pk}'>删除&nbsp;</a>"
        if not self.list_display_links:
            t.append(edit_p)
        t.append(dele_p)
        # 把operation_list子类重写的方法对象数组，添加到后面。
        t.extend(self.operation_list(obj))
        return mark_safe(" ".join(t))

    def checkbox(self, obj=None, is_header=False):
        if is_header:
            return mark_safe("<input id='choice' type='checkbox'>")
        return mark_safe(f"<input class='choice_itme' type='checkbox' name='selected_pk' value='{obj.pk}'>")

    def new_list_play(self):
        temp = []
        temp.append(ModelXadmin.checkbox)
        list_display = self.list_display
        temp.extend(list_display)
        # if not self.list_display_links:
        #     temp.append(ModelXadmin.edit)
        # temp.append(ModelXadmin.dele)
        temp.append(ModelXadmin.operation)
        return temp

    def new_actions(self):
        temp = []
        temp.append(ModelXadmin.path_delete)
        temp.extend(self.actions)
        return temp

    def get_modelform_class(self):
        if not self.modelform_class:
            from django.forms import ModelForm
            from django.forms import widgets as wid
            class ModelFormDemo(ModelForm):
                class Meta:
                    model = self.model
                    fields = "__all__"
            return ModelFormDemo
        else:
            return self.modelform_class

    def get_change_url(self, obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        pk = obj.pk
        _url = reverse(f"{app_label}_{model_name}_change", args=(pk,))
        return _url

    def get_list_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        _url = reverse(f"{app_label}_{model_name}_list")
        return _url

    def get_add_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        _url = reverse(f"{app_label}_{model_name}_add")
        return _url

    def get_del_url(self, obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        pk = obj.pk
        _url = reverse(f"{app_label}_{model_name}_del", args=(pk,))
        return _url

    def get_search_conditon(self, request):
        key = request.GET.get("q", "")
        self.key = key
        # 获得当前所有数据和创建的a标签链接

        search_Q = Q()
        if key:
            search_Q.connector = "or"
            for search_field in self.search_fields:
                search_Q.children.append((search_field + "__contains", key))

        return search_Q

    def get_filter_conditon(self, request):
        filter_condition = Q()
        for filter_field, val in request.GET.items():
            if filter_field !="page":
                filter_condition.children.append((filter_field, val))

        return filter_condition

    def add_view(self, request):

        ModelFormDemo = self.get_modelform_class()
        form = ModelFormDemo()
        if request.method == "POST":
            form = ModelFormDemo(request.POST)

            if form.is_valid():
                obj = form.save()  # modelform封装好的，保存到数据库中

                pop_res_id = request.GET.get("pop_res_id")
                if pop_res_id:
                    print(pop_res_id)
                    res = {"pk": obj.pk, "text": str(obj), "eid": pop_res_id}
                    return render(request, "pop.html", locals())
                else:
                    return redirect(self.get_list_url())
        # form
        # d_list = []
        # for f in form.fields:
        #     f_obj = self.model._meta.get_field(f)
        #     if f_obj.rel:
        #         d_list.append(f)
        for f in form:  # form对象值，为models生成的属性对象。
            # from django.forms.boundfield import BoundField
            from django.forms.models import ModelChoiceField
            if isinstance(f.field, ModelChoiceField):
                f.is_pop = True  # 一对一，一对多或多对多，对象.名称赋值就能对一个属性。
                # print(f.name)  字段的名称，通过名称获取对应的关联表对象。
                f_to_obj = f.field.queryset.model  # 获得一对多或多对多关联表的对象的模型信息
                # print(f_to_obj)
                app_label=f_to_obj._meta.app_label
                model_name=f_to_obj._meta.model_name  # 已经进入关联表中获得管理表对象的表名字
                _url = reverse(f"{app_label}_{model_name}_add")
                print("f.name-->",f.name, "model_name-->", model_name)
                print("f.name-->",type(f), "model_name-->", type(f_to_obj))
                f.url = _url+f"?pop_res_id=id_{f.name}"

        # print(locals())
        return render(request, "add_view.html", locals())

    def change_view(self, request, id):
        ModelFormDemo = self.get_modelform_class()
        edit_obj = self.model.objects.filter(pk=id).first()
        if request.method == "POST":
            form = ModelFormDemo(request.POST, instance=edit_obj)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            return render(request, "change_view.html", locals())
        form = ModelFormDemo(instance=edit_obj)
        return render(request, "change_view.html", locals())

    def del_view(self, request, id):
        # models01.Book.objects.filter().
        ret = {"status": 0, "msg": ""}
        if request.method == "POST":
            self.model.objects.filter(pk=id).delete()
            ret["msg"] = self.get_list_url()
        else:
            ret["status"]=1
            ret["msg"] = "删除失败"
        return JsonResponse(ret)

    def list_view(self, request):
        if request.method == "POST":

            action = request.POST.get("action")  # 获得方法名称的字符串
            selected_pk = request.POST.getlist("selected_pk")
            if action:
                action_func = getattr(self, action)  # 通过反射获得方法对象，在进行调用。
                queryset = self.model.objects.filter(pk__in=selected_pk)
                action_func(request, queryset)
            print(request.POST)

        list_display = self.new_list_play()

        # 获取筛选Q对象的信息
        search_Q = self.get_search_conditon(request)
        # 获得filter构建Q对象
        filter_Q = self.get_filter_conditon(request)

        # 按照showlist展示数据列表页面(添加筛选Q方法的数据)
        data_list = self.model.objects.all().filter(search_Q).filter(filter_Q)
        show_list = ShowList(self, data_list, request, list_display)


        return render(request, "list_view.html", locals())
    # 让子类去继承重写该方法，来添加URL用
    def extra_url(self):
        return []

    def get_urls_2(self):
        temp = []
        # 设置反向解析的URL链接，利用别名进行后续调用
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        temp.append(url(r'^$', self.list_view, name=f'{app_label}_{model_name}_list'))
        temp.append(url(r'^add/$', self.add_view, name=f'{app_label}_{model_name}_add'))
        temp.append(url(r'^(\d+)/change/$', self.change_view, name=f'{app_label}_{model_name}_change'))
        temp.append(url(r'^(\d+)/del/$', self.del_view, name=f'{app_label}_{model_name}_del'))

        temp.extend(self.extra_url())
        return temp
    @property
    def urls_2(self):
        return self.get_urls_2(), None, None

# 全局类 （注册、链接）
class XadminSite(object):
    def __init__(self, name='admin'):
        self._registry = {}


    def get_urls(self):
        temp = []
        for model, admin_class_obj in self._registry.items():
            app_name = model._meta.app_label
            model_name = model._meta.model_name
            temp.append(url(r'^{0}/{1}/'.format(app_name, model_name), admin_class_obj.urls_2, name="1"))
        #  url(r"^demo001/book/", ModelXadmin(Book).urls2)
        #  url(r"^demo002/Order/", ModelXadmin(Order).urls2)
        return temp

    @property  # 静态方法标签
    def urls(self):

        return self.get_urls(), None, None

    def register(self, model, admin_class=None, **options):
        if not admin_class:
            admin_class = ModelXadmin
        self._registry[model] = admin_class(model, self)


site = XadminSite()


