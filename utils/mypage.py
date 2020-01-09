class Page():
    def __init__(self,page_num, total_count, url_prefix, per_page=10, max_page = 5):
        """
               :param page_num: 当前页码数
               :param total_count: 数据总数
               :param url_prefix: a标签href的前缀
               :param per_page: 每页显示多少条数据
               :param max_page: 页面上最多显示几个页码
        """
        self.url_prefix = url_prefix
        self.page_num = page_num
        self.max_page = max_page
        total_page, m = divmod(total_count, per_page)
        if m:
            total_page += 1
        self.total_page = total_page
        try:
            page_num = int(page_num)
            if total_page < self.max_page:
                self.max_page = total_page
            if total_page < page_num:
                page_num = 1
        except Exception as e:
            # 当输入的页面不是真正数字的时候，默认返回第一页的数据
            page_num = 1
        self.page_num = page_num
        # 定义两个变量保存数据从那取到哪儿
        self.data_start = (page_num - 1) * 10
        self.data_end = page_num * 10

        half_max_page = self.max_page // 2
        # 页面上展示的页面从哪开始

        page_start = page_num - half_max_page
        # 页面上展示的页面到哪结束
        page_end = page_num + half_max_page

        if page_start <= 1:
            page_start = 1
            page_end = self.max_page
        if page_end >= total_page:
            page_start = total_page - self.max_page + 1
            page_end = total_page
        self.page_start=page_start
        self.page_end = page_end

    @property
    def start(self):
        return self.data_start

    @property
    def end(self):
        return self.data_end

    def page_html(self):
        html_str_list = []

        # 加上第一页
        html_str_list.append('<li><a href="{0}?page=1">首页</a></li>'.format(self.url_prefix))
        if self.page_num > 1:
            html_str_list.append('<li><a href="{0}?page={1}">上一页</a></li>'.format(self.url_prefix, self.page_num - 1))

        for i in range(self.page_start, self.page_end + 1):
            if i == self.page_num:
                tmp = '<li class="active"><a href="{0}?page={1}">{1}</a></li>'.format(self.url_prefix, i)
            else:
                tmp = '<li><a href="{0}?page={1}">{1}</a></li>'.format(self.url_prefix, i)
            html_str_list.append(tmp)
        # 加上下一页
        if self.page_num < self.total_page:
            html_str_list.append('<li><a href="{0}?page={1}">下一页</a></li>'.format(self.url_prefix, self.page_num + 1))
        # 加上尾页
        html_str_list.append('<li><a href="{0}?page={1}">尾页</a></li>'.format(self.url_prefix, self.total_page))

        page_html = ''.join(html_str_list)
        return page_html

