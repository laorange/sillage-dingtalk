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

    def filter_of_date(self, date: str):
        def courseFiler(c: Course) -> bool:
            return date in c.dates

        return self.filter(courseFiler)

    def filter_of_methods(self, methods: List[str]):
        def courseFiler(c: Course) -> bool:
            return c.method in methods

        return self.filter(courseFiler)

    def filter_of_teachers(self, teachers: List[str]):
        def courseFiler(c: Course) -> bool:
            teacher_list = list(map(lambda gg: gg[0].teacher, c.situations))
            return whether_two_list_have_same_element(teacher_list, teachers)

        return self.filter(courseFiler)

    def filter_of_course_names(self, course_names: List[str]):
        def courseFiler(c: Course) -> bool:
            return c.info.name in course_names

        return self.filter(courseFiler)

    def filter_of_rooms(self, rooms: List[str]):
        def courseFiler(c: Course) -> bool:
            room_list = list(map(lambda gg: gg[0].room, c.situations))
            return whether_two_list_have_same_element(room_list, rooms)

        return self.filter(courseFiler)

    def __str__(self):
        def decorateStr(s: str):
            return s + "\n" if s else ""

        def getCourseStr(c: Course):
            courseStr = ""
            courseStr += decorateStr(c.info.name)
            courseStr += decorateStr(c.method)
            if len(c.situations) == 1:
                situ = c.situations[0]
                courseStr += "".join([decorateStr("丨".join(situ.groups) if situ.groups else ""), decorateStr(situ.teacher), decorateStr(situ.room)])
            elif len(c.situations) > 1:
                courseStr += "丨".join([decorateStr("丨".join(situ.groups) if situ.groups else "") + decorateStr(situ.teacher) + decorateStr(situ.room)
                                       for situ in c.situations])
            courseStr += decorateStr(c.note)
            return courseStr

        # -----------
        lessonNumStrList: List[str] = []

        for lessonNum in range(1, 6):
            lessonNumStr = ""
            coursesOfLessonNum = self.filter_of_lesson_num(lessonNum).value
            if len(coursesOfLessonNum):
                lessonNumStr += f"第 {lessonNum} 节课：\n"
                lessonNumStr += "\n\n".join([getCourseStr(c) for c in coursesOfLessonNum])
                lessonNumStrList.append(lessonNumStr.strip())
        return f"\n{'-' * 8}\n".join(lessonNumStrList)


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
