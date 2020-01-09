# by luffycity.com

from stark.service.stark import site, ModelXadmin
from .models import *
from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import HttpResponse, redirect, render
from django.http import JsonResponse
site.register(School)

class UserConfig(ModelXadmin):
    list_display = ["name", "email", "depart"]

site.register(UserInfo,UserConfig)


class ClassConfig(ModelXadmin):


    def display_classname(self,obj=None,is_header=False):
        if is_header:
            return "班级名称"
        class_name="%s(%s)"%(obj.course.name,str(obj.semester))
        return class_name

    list_display = [display_classname,"tutor","teachers"]


site.register(ClassList,ClassConfig)




class CusotmerConfig(ModelXadmin):

    def display_gender(self,obj=None,is_header=False):
        if is_header:
            return "性别"
        return obj.get_gender_display()

    def display_course(self,obj=None,is_header=False):
        if is_header:
            return "咨询课程"
        temp = []
        for course in obj.course.all():
            #
            s = f"<a href='/stark/crm/customer/cancel_course/{obj.pk}/{course.pk}' style='border:1px solid #369;padding:3px 6px'><span>{course.name}</span></a>&nbsp;"
            temp.append(s)
        return mark_safe("".join(temp))

    list_display = ["name", display_gender, display_course, "consultant"]

    def cancel_course(self, request, customer_id, course_id):
        # print(customer_id,course_id)
        obj=Customer.objects.filter(pk=customer_id).first()
        obj.course.remove(course_id)
        return redirect(self.get_list_url())

    def public_customer(self, requset):
        # 未报名，且3天未跟进或者15天未成单
        # 3天未跟进：now-last_consult_date>3  --- last_consult_date<now-3 3天使用 datetime.timedelta(days=3)
        # 15天未成单：now-recv_date>15  --- recv_date<now-15 15天未成单 datetime.timedelta(days=15)
        import datetime

        """
        datetime四个类：
        datetime.datetime --年月日时分秒
        datetime.date --时分秒
        datetime.time --年月日
        datetime.timedelta() --时间片
        """
        now = datetime.datetime.now()
        delta_day3 = datetime.timedelta(days=3)
        delta_day15 = datetime.timedelta(days=15)
        from django.db.models import Q  # 或的连接符号。且的连接符号用“,”。两个同时出现时有顺序问题或方前面不会报错。
        customer_list = Customer.objects.filter(Q(last_consult_date__lt=now-delta_day3)|Q(recv_date__lt=now-delta_day15), status=2)
        print(customer_list)
        return render(requset, "public.html",locals())

    # 添加新的URL信息
    def extra_url(self):

        temp=[]

        temp.append(url(r"cancel_course/(\d+)/(\d+)", self.cancel_course))
        temp.append(url(r"public/", self.public_customer))

        return temp

site.register(Customer,CusotmerConfig)

class ConsultRecordConfig(ModelXadmin):
    list_display = ["customer", "consultant", "date", "note"]

site.register(ConsultRecord, ConsultRecordConfig)

class StudentConfig(ModelXadmin):

    def score_view(self, request, sid):
        if request.is_ajax():
            # print(request.GET)
            sid = request.GET.get("sid")
            cid = request.GET.get("cid")
            student_record_list = StudyRecord.objects.filter(student=sid, course_record__class_obj=cid)
            print(student_record_list)
            data_list = []
            for student_record in student_record_list:
                day_num = student_record.course_record.day_num
                data_list.append([f"day{day_num}", student_record.score])
            return JsonResponse(data_list, safe=False)

        else:
            student = Student.objects.filter(pk=sid).first()
            class_list = student.class_list.all()
            return render(request, "score.html", locals())

    def extra_url(self):
        temp=[]
        temp.append(url(r"score_view/(\d+)", self.score_view))
        return temp

    def score_show(self, obj=None, is_header=False):
        if is_header:
            return "查看成绩"
        return mark_safe("<a href='score_view/%s'>查看成绩</a>" % obj.pk)



    list_display = ["customer", "class_list", score_show]
    list_display_links = ["customer"]

site.register(Student, StudentConfig)

site.register(Department)
site.register(Course)

class CourseRecordConfig(ModelXadmin):
    list_display = ["class_obj", "day_num", "teacher"]

    def patch_studyrecord(self, request, queryset):
        # print(queryset)
        temp = []
        for course_record in queryset:
            # 与course_record关联的班级的所有学生。
            student_list = Student.objects.filter(class_list__id=course_record.class_obj.pk)
            for student in student_list:
                obj = StudyRecord(student=student, course_record=course_record)
                temp.append(obj)
        StudyRecord.objects.bulk_create(temp)
    # 继承父类并重写operation_list方法，添加想要的字段信息。
    def operation_list(self, obj):
        t = []
        sign_in = f"<a href='/stark/crm/studyrecord/?course_record={obj.pk}'>签到&nbsp;</a>"
        score = f"<a href='/stark/crm/courserecord/{obj.pk}/record_score'>录入成绩</a>"
        t.append(sign_in)
        t.append(score)
        return t

    def record_score(self, request, classlist_id):

        if request.method == "POST":
            dic_str = {}
            # 数据库优化通过字典的形式进行：{'15': {'score': '85', 'homework_note': '345手动'}, '16': {'score': '50', 'homework_note': '1234十点多'}}
            # 构造数据格式为对象pk值，跟更新字段的字典信息。传入sql执行语句。
            for key, value in request.POST.items():
                if key == "csrfmiddlewaretoken":
                    continue
                field, pk = key.rsplit("_", 1)  # 从右边开始切割
                print(field)
                if pk in dic_str:
                    dic_str[pk][field] = value
                else:
                    dic_str[pk] = {field: value}

                # dic_str[pk] = dict(dic_score, **dic_text)  # 合并字典数据
            print(dic_str)
            for pk, update_val in dic_str.items():
                sr_obj = StudyRecord.objects.filter(pk=pk).update(**update_val)
                # # field_obj = getattr(sr_obj,field)
                # print(field, value)
                # if field == "score":
                #     sr_obj.update(score=value)
                # else:
                #     sr_obj.update(homework_note=value)


            return redirect(request.path)
        else:
            studyrecord_obj = StudyRecord.objects.filter(course_record=classlist_id)
            # for studyrecord in studyrecord_obj:
            score_choices = StudyRecord.score_choices

            return render(request, "score_view.html", locals())



    def extra_url(self):

        temp=[]

        temp.append(url(r"(\d+)/record_score", self.record_score))

        return temp

    patch_studyrecord.short_description = "批量生成学习记录"
    actions = [patch_studyrecord]

site.register(CourseRecord, CourseRecordConfig)

class StudyRecordConfig(ModelXadmin):

    # def display_record(self, obj=None, is_header=False):
    #     if is_header:
    #         return "上课记录"
    #     return obj.get_record_display()
    #
    # def display_score(self, obj=None, is_header=False):
    #     if is_header:
    #         return "上课记录"
    #     return obj.get_record_display()

    def check_on(self, obj=None, is_header=False):
        if is_header:
            return "上课记录"
        record_choices = StudyRecord.record_choices
        temp = []
        for record in record_choices:
            if obj.record == record[0]:
                score_a = f"<button class='record btn btn-primary' obj_id='{obj.pk}' record_id='{record[0]}'>{record[1]}&nbsp;</button>"
            # print(score[0], score[1])
            else:
                score_a = f"<button class='record btn btn-default' obj_id='{obj.pk}' record_id='{record[0]}'>{record[1]}&nbsp;</button>"
            temp.append(score_a)
        return mark_safe(" ".join(temp))

    def record_editor(self, request):
        ret = {"status": 0, "msg": ""}
        if request.method == "POST":
            record_id = request.POST.get("record_id")
            obj_id = request.POST.get("obj_id")
            StudyRecord.objects.filter(pk=obj_id).update(record=record_id)
            ret["msg"] = self.get_list_url()
        else:
            ret["status"] = 1
            ret["msg"] = "更新失败"
        return JsonResponse(ret)


    def extra_url(self):
        temp = []
        temp.append(url(r"record", self.record_editor))

        return temp


    list_display = ["student", "course_record", "record", "score", check_on]
    list_filter = ["course_record"]

    def patch_late(self, request, queryset):
        queryset.update(record="late")

    patch_late.short_description = "批量迟到"
    actions = [patch_late]






site.register(StudyRecord, StudyRecordConfig)


