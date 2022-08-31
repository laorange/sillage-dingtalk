from utils.course.apiHandler import ApiHandler
from apscheduler.schedulers.background import BlockingScheduler


def job_function():
    print("{{对应的推送内容}}")


if __name__ == '__main__':
    # apiHandler = ApiHandler()
    scheduler = BlockingScheduler()
    scheduler.add_job(job_function, 'cron', hour=6, minute=00)
    scheduler.add_job(job_function, 'cron', hour=7, minute=30)
    scheduler.add_job(job_function, 'cron', hour=9, minute=35)
    scheduler.add_job(job_function, 'cron', hour=11, minute=40)
    scheduler.add_job(job_function, 'cron', hour=15, minute=5)
    scheduler.add_job(job_function, 'cron', hour=17, minute=10)
    scheduler.add_job(job_function, 'cron', hour=17, minute=30)
    scheduler.start()
    # breakpoint()
