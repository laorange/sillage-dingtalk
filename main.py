import asyncio
import re
from typing import List
from urllib.parse import urlparse, parse_qs

from apscheduler.schedulers.background import BlockingScheduler

from utils.course import apiHandler, CourseDecorator
from utils.dingtalk import dingTalkHandler


class UserHandler:
    def __init__(self, userId: str, subscribedUrl: str):
        self.userId = userId
        self.subscribedUrl = subscribedUrl

    def getCourseDecorator(self) -> CourseDecorator:
        urlParseResult = urlparse(SillageDingtalkHandler.urlStrip(self.subscribedUrl))
        queryParseResult = parse_qs(urlParseResult.query)

        # TODO: 课程过滤
        ...

        return apiHandler.courseDecorator

    def sendCorporationTextMsg(self, msg: str):
        asyncio.run(dingTalkHandler.sendCorporationTextMsg([self.userId], msg))


class SillageDingtalkHandler:
    def __init__(self):
        userTupleList = dingTalkHandler.getSillageUserAndUrlList()
        self.users: List[UserHandler] = [UserHandler(userTuple[0].submitterUserId, userTuple[1]) for userTuple in userTupleList]

        self.scheduler = BlockingScheduler()
        self.scheduler.add_job(self.job_function, 'cron', hour=6, minute=00)
        self.scheduler.add_job(self.job_function, 'cron', hour=7, minute=30)
        self.scheduler.add_job(self.job_function, 'cron', hour=9, minute=35)
        self.scheduler.add_job(self.job_function, 'cron', hour=11, minute=40)
        self.scheduler.add_job(self.job_function, 'cron', hour=15, minute=5)
        self.scheduler.add_job(self.job_function, 'cron', hour=17, minute=10)
        self.scheduler.add_job(self.job_function, 'cron', hour=17, minute=30)
        self.scheduler.add_job(self.job_function, 'cron', hour=21, minute=39)

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown(wait=True)

    def job_function(self):
        print("TODO: 发送课程信息")

    def sendCoursesOfLessonNum(self, lessonNum: int):
        ...

    def sendCourseOfDate(self, date: str):
        ...

    @staticmethod
    def urlStrip(url: str):
        return re.sub(r"https?://[a-z]+\.siae.top/#/", "", url)


if __name__ == '__main__':
    mainHandler = SillageDingtalkHandler()
    mainHandler.start()
