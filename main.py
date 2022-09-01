import asyncio
import datetime
import re
from typing import List
from functools import partial

from apscheduler.schedulers.background import BlockingScheduler

from urllib.parse import urlparse, parse_qs
from utils.course import apiHandler, CourseDecorator, QueryParseResult
from utils.dingtalk import dingTalkHandler


class UserHandler:
    def __init__(self, userId: str, subscribedUrl: str):
        self.userId = userId
        self.subscribedUrl = subscribedUrl

    def getCourseDecorator(self) -> CourseDecorator:
        urlParseResult = urlparse(SillageDingtalkHandler.urlStrip(self.subscribedUrl))
        queryParseResult = QueryParseResult(**parse_qs(urlParseResult.query))

        courseDecorator = apiHandler.courseDecorator
        courseDecorator = courseDecorator.filter_grades(queryParseResult.grade) if queryParseResult.grade else courseDecorator
        courseDecorator = courseDecorator.filter_of_rooms(queryParseResult.room) if queryParseResult.room else courseDecorator
        courseDecorator = courseDecorator.filter_of_methods(queryParseResult.method) if queryParseResult.method else courseDecorator
        courseDecorator = courseDecorator.filter_of_teachers(queryParseResult.teacher) if queryParseResult.teacher else courseDecorator
        courseDecorator = courseDecorator.filter_of_grade_groups(queryParseResult.group) if queryParseResult.group else courseDecorator
        courseDecorator = courseDecorator.filter_of_course_names(queryParseResult.subject) if queryParseResult.subject else courseDecorator

        return courseDecorator

    def sendCorporationTextMsg(self, msg: str):
        asyncio.run(dingTalkHandler.sendCorporationTextMsg([self.userId], msg))


class SillageDingtalkHandler:
    def __init__(self):
        userTupleList = dingTalkHandler.getSillageUserAndUrlList()
        self.users: List[UserHandler] = [UserHandler(userTuple[0].submitterUserId, userTuple[1]) for userTuple in userTupleList]

        today = datetime.datetime.today()
        getTodayHM = lambda hour, minute: datetime.datetime(today.year, today.month, today.day, hour, minute)

        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(self.goodMorning, "date", next_run_time=getTodayHM(6, 0))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 1), "date", next_run_time=getTodayHM(7, 30))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 2), "date", next_run_time=getTodayHM(9, 35))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 3), "date", next_run_time=getTodayHM(11, 40))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 4), 'date', next_run_time=getTodayHM(15, 5))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 5), 'date', next_run_time=getTodayHM(17, 10))
        self.scheduler.add_job(self.goodNight, "date", next_run_time=getTodayHM(17, 30))

        # TODO: 调试完成后删除本段
        self.scheduler.add_job(self.goodMorning, "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=3))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 1), "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=4))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 2), "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=5))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 3), "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=6))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 4), 'date', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=7))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 5), 'date', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=8))
        self.scheduler.add_job(self.goodNight, "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=9))

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown(wait=True)

    def goodMorning(self):
        todayDate = datetime.date.today().strftime("%Y-%m-%d")
        self.sendCourseOfDate(todayDate, dateDescription=f"今天({todayDate})")

    def goodNight(self):
        tomorrowDate = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.sendCourseOfDate(tomorrowDate, f"明天({tomorrowDate})")

    def sendCoursesOfLessonNum(self, lessonNum: int, date: str = ""):
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")  # 默认为今天

        for user in self.users:
            courseDecoratorOfThisLessonNum = user.getCourseDecorator().filter_of_date(date).filter_of_lesson_num(lessonNum)
            if len(courseDecoratorOfThisLessonNum.value):
                user.sendCorporationTextMsg(f"{str(courseDecoratorOfThisLessonNum).strip()}"
                                            f"\n{'-' * 8}\n发送时间：{datetime.datetime.now().strftime('%H:%M:%S')}")

    def sendCourseOfDate(self, date: str, dateDescription: str = "今天：", addition: str = ""):
        for user in self.users:
            courseDecoratorOfThisDate = user.getCourseDecorator().filter_of_date(date)
            if len(courseDecoratorOfThisDate.value):
                user.sendCorporationTextMsg(f"{dateDescription}\n{str(courseDecoratorOfThisDate).strip()}"
                                            f"\n{'-' * 8}\n发送时间：{datetime.datetime.now().strftime('%H:%M:%S')}")

    @staticmethod
    def urlStrip(url: str):
        return re.sub(r"https?://[a-z]+\.siae.top/#/", "", url)


if __name__ == '__main__':
    mainHandler = SillageDingtalkHandler()
    mainHandler.start()
