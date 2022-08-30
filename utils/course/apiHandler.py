import json
import math
from typing import List, Callable, Tuple

import httpx

from utils.course.types import Course

CourseFilter = Callable[[Course], bool]


def whether_two_list_have_same_element(list_a: List, list_b: List):
    return bool(len([a for a in list_a if a in list_b]))


class CourseDecorator:
    def __init__(self, courses: List[Course]):
        self.value: List[Course] = courses

    def filter(self, filter_function: CourseFilter):
        return CourseDecorator(list(filter(filter_function, self.value)))

    def filter_grades(self, grades: List[str]):
        def courseFilter(c: Course) -> bool:
            return c.grade in grades

        return self.filter(courseFilter)

    def filter_of_lesson_num(self, lesson_number: int):
        def courseFilter(c: Course) -> bool:
            return c.lessonNum == lesson_number

        return self.filter(courseFilter)

    def filter_of_grade_groups(self, grade_groups: List[str]):
        grade_groups: List[Tuple[str, str]] = list(map(lambda gg: json.loads(gg), grade_groups))
        grades = list(map(lambda gg: gg[0], grade_groups))

        def courseFiler(c: Course) -> bool:
            for situation in c.situations:
                if len(situation.groups) == 0:
                    # 如果某节课没有指定“班级/小组”，则按年级，则符合条件
                    return True
                groups_of_this_grade = list(map(lambda gg: gg[1], filter(lambda gg: gg[0] == c.grade, grade_groups)))
                # 如果该课程的某 situation.groups 与需要的 groups 有重叠，则符合条件
                if whether_two_list_have_same_element(situation.groups, groups_of_this_grade):
                    return True
            return False

        return self.filter_grades(grades).filter(courseFiler)

    # def filter_room(self, room):
    #     temp_infos = self.infos[:]
    #     for each in self.infos:
    #         if each['situations'][0]['room'] != room:
    #             temp_infos.remove(each)
    #     return temp_infos
    #
    # def filter_method(self, method):
    #     temp_infos = self.infos[:]
    #     for each in self.infos:
    #         if each['method'] != method:
    #             temp_infos.remove(each)
    #     return temp_infos
    #
    # def filter_teacher(self, teacher):
    #     temp_infos = self.infos[:]
    #     for each in self.infos:
    #         if each['situations'][0]['teacher'] != teacher:
    #             temp_infos.remove(each)
    #     return temp_infos
    #
    # def filter_group(self, group):
    #     temp_infos = self.infos[:]
    #     for each in self.infos:
    #         if (group[0] not in each['situations'][0]['groups']) or (group[1] not in each['situations'][0]['groups']):
    #             temp_infos.remove(each)
    #     return temp_infos
    #
    # def filter_subject(self, subject):
    #     temp_infos = self.infos[:]
    #     for each in self.infos:
    #         if each['info'][0]['name'] != subject:
    #             temp_infos.remove(each)
    #     return temp_infos


class ApiHandler:
    base_url = 'https://sillage.siae.top/api/collections/course/records'
    max_per_page = 200
    courseDecorator: CourseDecorator

    def __init__(self):
        res = httpx.get(self.base_url, params=dict(page=1, perPage=1, sort="-updated"))
        totalItems = res.json()['totalItems']

        rawCourses = []
        for i in range(math.ceil(totalItems / 200)):
            res = httpx.get(self.base_url, params=dict(page=i + 1, perPage=self.max_per_page, sort="-updated"))
            items = res.json()['items']
            rawCourses += items

        self.courseDecorator = CourseDecorator([Course(**rawCourse) for rawCourse in rawCourses])
