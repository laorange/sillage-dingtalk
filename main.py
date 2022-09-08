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

    def sendCorporationMsg(self, msg: str, title="课程提醒"):
        asyncio.run(dingTalkHandler.sendCorporationMarkdownMsg([self.userId], title=title, text=msg))


class SillageDingtalkHandler:
    def __init__(self):
        self.users: List[UserHandler] = self.getUsers()
        self.scheduler = BlockingScheduler()

    @staticmethod
    def getTodayHM(hour, minute):
        today = datetime.datetime.today()
        return datetime.datetime(today.year, today.month, today.day, hour, minute)

    @staticmethod
    def getUsers() -> List[UserHandler]:
        userTupleList = dingTalkHandler.getSillageUserAndUrlList()
        return [UserHandler(userTuple[0].submitterUserId, userTuple[1]) for userTuple in userTupleList]

    def refreshUsers(self):
        self.users: List[UserHandler] = self.getUsers()

    def start(self):
        self.scheduler.add_job(self.refreshRemoteData, 'interval', hours=1)  # 每隔一个小时，刷新一次远端数据
        self.scheduler.add_job(self.goodMorning, "date", next_run_time=self.getTodayHM(6, 0), misfire_grace_time=600)
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 1), "date", next_run_time=self.getTodayHM(7, 30), misfire_grace_time=600)
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 2), "date", next_run_time=self.getTodayHM(9, 35), misfire_grace_time=600)
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 3), "date", next_run_time=self.getTodayHM(11, 40), misfire_grace_time=600)
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 4), 'date', next_run_time=self.getTodayHM(15, 5), misfire_grace_time=600)
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 5), 'date', next_run_time=self.getTodayHM(17, 10), misfire_grace_time=600)
        self.scheduler.add_job(self.goodNight, "date", next_run_time=self.getTodayHM(17, 30), misfire_grace_time=600)

        self.scheduler.start()

    def test(self):
        user: List[UserHandler] = self.users[:1]
        self.scheduler.add_job(partial(self.goodMorning, sendDateTime=True, users=user), "date",
                               next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=3))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 1, sendDateTime=True, users=user), "date",
                               next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=4))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 2, sendDateTime=True, users=user), "date",
                               next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=5))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 3, sendDateTime=True, users=user), "date",
                               next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=6))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 4, sendDateTime=True, users=user), 'date',
                               next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=7))
        self.scheduler.add_job(partial(self.sendCoursesOfLessonNum, 5, sendDateTime=True, users=user), 'date',
                               next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=8))
        self.scheduler.add_job(partial(self.goodNight, sendDateTime=True, users=user), "date",
                               next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=9))

        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown(wait=False)

    def refreshRemoteData(self):
        """刷新AccessToken、重新获取课程、重新获取订阅用户列表"""
        dingTalkHandler.accessToken = dingTalkHandler.getAccessToken()
        apiHandler.refreshCourses()
        self.refreshUsers()

    def goodMorning(self, addition: str = "更多信息: course.siae.top", sendDateTime: bool = False, users: List[UserHandler] = None):
        todayDate = datetime.date.today().strftime("%Y-%m-%d")
        self.sendCourseOfDate(todayDate, dateDescription=f"今天({todayDate})", sendDateTime=sendDateTime, addition=addition, users=users)

    def goodNight(self, addition: str = "更多信息: course.siae.top", sendDateTime: bool = False, users: List[UserHandler] = None):
        tomorrowDate = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.sendCourseOfDate(tomorrowDate, f"明天({tomorrowDate})", sendDateTime=sendDateTime, addition=addition, users=users)
        self.shutdown()

    @logger.catch
    def sendCoursesOfLessonNum(self, lessonNum: int, date: str = "", addition: str = "", sendDateTime: bool = False, users: List[UserHandler] = None):
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")  # 默认为今天

        if not users:
            users = self.users

        for user in users:
            courseDecoratorOfThisLessonNum = user.getCourseDecorator().filter_of_date(date).filter_of_lesson_num(lessonNum)
            if len(courseDecoratorOfThisLessonNum.value):
                msg = f"{str(courseDecoratorOfThisLessonNum).strip()}"
                msg += f"\n\n{'-' * 8}\n\n{addition}" if addition else ""
                msg += f"\n\n{'-' * 8}\n\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" if sendDateTime else ""

                title = "丨".join([f"{course.info.name}:"
                                  f"{','.join(['-'.join([_ for _ in ['&'.join(situ.groups), situ.room] if _]) for situ in course.situations])}"
                                  for course in courseDecoratorOfThisLessonNum.value])

                user.sendCorporationMsg(msg, title=title)

    @logger.catch
    def sendCourseOfDate(self, date: str, dateDescription: str = "今天：", addition: str = "", sendDateTime: bool = False,
                         users: List[UserHandler] = None):
        if not users:
            users = self.users

        for user in users:
            courseDecoratorOfThisDate = user.getCourseDecorator().filter_of_date(date)
            if len(courseDecoratorOfThisDate.value):
                msg = f"{dateDescription}\n\n{str(courseDecoratorOfThisDate).strip()}"
                msg += f"\n\n{'-' * 8}\n\n{addition}" if addition else ""
                msg += f"\n\n{'-' * 8}\n\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" if sendDateTime else ""

                title = f"{dateDescription}有{len(courseDecoratorOfThisDate.value)}节课"
                user.sendCorporationMsg(msg, title=title)

    @staticmethod
    def urlStrip(url: str):
        return re.sub(r"https?://[a-z]+\.siae.top/#/", "", url)


if __name__ == '__main__':
    mainHandler = SillageDingtalkHandler()
    # mainHandler.test()
    mainHandler.start()
