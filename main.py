import asyncio
import datetime
import re
from typing import List
from functools import partial
from urllib.parse import urlparse, parse_qs

from apscheduler.schedulers.background import BlockingScheduler
from loguru import logger

logger.add("log/file_{time}.log", rotation="04:00", retention="10 days", level="INFO")

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

    def sendCorporationMsg(self, msg: str):
        asyncio.run(dingTalkHandler.sendCorporationMarkdownMsg([self.userId], title="课程提醒", text=msg))


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

        # # 调试用
        # self.scheduler.add_job(self.goodMorning, "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=3))
        # self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 1), "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=4))
        # self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 2), "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=5))
        # self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 3), "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=6))
        # self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 4), 'date', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=7))
        # self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 5), 'date', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=8))
        # self.scheduler.add_job(self.goodNight, "date", next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=9))

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown(wait=False)

    def goodMorning(self):
        todayDate = datetime.date.today().strftime("%Y-%m-%d")
        self.sendCourseOfDate(todayDate, dateDescription=f"今天({todayDate})")

    def goodNight(self):
        tomorrowDate = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.sendCourseOfDate(tomorrowDate, f"明天({tomorrowDate})")
        self.shutdown()

    @logger.catch
    def sendCoursesOfLessonNum(self, lessonNum: int, date: str = ""):
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")  # 默认为今天

        for user in self.users:
            courseDecoratorOfThisLessonNum = user.getCourseDecorator().filter_of_date(date).filter_of_lesson_num(lessonNum)
            if len(courseDecoratorOfThisLessonNum.value):
                msg = f"{str(courseDecoratorOfThisLessonNum).strip()}" \
                      f"\n\n{'-' * 8}\n\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"  # 调试用
                user.sendCorporationMsg(msg)

    @logger.catch
    def sendCourseOfDate(self, date: str, dateDescription: str = "今天："):
        for user in self.users:
            courseDecoratorOfThisDate = user.getCourseDecorator().filter_of_date(date)
            if len(courseDecoratorOfThisDate.value):
                msg = f"{dateDescription}\n\n{str(courseDecoratorOfThisDate).strip()}" \
                      f"\n\n{'-' * 8}\n\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"  # 调试用
                user.sendCorporationMsg(msg)

    @staticmethod
    def urlStrip(url: str):
        return re.sub(r"https?://[a-z]+\.siae.top/#/", "", url)


if __name__ == '__main__':
    mainHandler = SillageDingtalkHandler()
    mainHandler.start()
