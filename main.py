from utils.course.apiHandler import ApiHandler
from apscheduler.schedulers.background import BlockingScheduler


def job_function():
    print("{{对应的推送内容}}")


if __name__ == '__main__':
    # apiHandler = ApiHandler()
    scheduler = BlockingScheduler()
    scheduler.add_job(job_function, 'cron', hour=5, minute=50)
    scheduler.add_job(job_function, 'cron', hour=7, minute=20)
    scheduler.add_job(job_function, 'cron', hour=9, minute=25)
    scheduler.add_job(job_function, 'cron', hour=11, minute=30)
    scheduler.add_job(job_function, 'cron', hour=14, minute=55)
    scheduler.add_job(job_function, 'cron', hour=17)
    scheduler.add_job(job_function, 'cron', hour=17, minute=20)
    scheduler.start()
    # breakpoint()
