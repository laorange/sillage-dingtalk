import math
from typing import List, Callable

import httpx

from utils.course.types import Course

CourseFilter = Callable[[Course], bool]


class CourseDecorator:
    def __init__(self, courses: List[Course]):
        self.value: List[Course] = courses

    def filter(self, filter_function: CourseFilter):
        return CourseDecorator(list(filter(filter_function, self.value)))

    def filter_grades(self, grades: List[str]):
        def courseFilter(c: Course) -> bool:
            return c.grade in grades

        return self.filter(courseFilter)

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
