import math

import requests

from pydantic import BaseModel


class JsonUsed(BaseModel):
    grade: str
    room: str
    method: str
    teacher: str
    group: [str, str]
    subject: str


class CourseHandler:
    base_url = 'https://sillage.siae.top/api/collections/course/records'
    max_per_page = 200
    infos = []

    def __init__(self):
        url = 'https://sillage.siae.top/api/collections/course/records?page=1&perPage=1&sort=-updated'
        res = requests.get(url)
        totalItems = res.json()['totalItems']
        for i in range(math.ceil(totalItems / 200)):
            res = requests.get(self.base_url + f'?page={i + 1}&perPage={self.max_per_page}&sort=-updated')
            items = res.json()['items']
            self.infos += items
        print(self.infos[1])

    def filter_grade(self, grade):
        temp_infos = self.infos[:]
        for each in self.infos:
            if each['grade'] != grade:
                temp_infos.remove(each)
        return temp_infos

    def filter_room(self, room):
        temp_infos = self.infos[:]
        for each in self.infos:
            if each['situations'][0]['room'] != room:
                temp_infos.remove(each)
        return temp_infos

    def filter_method(self, method):
        temp_infos = self.infos[:]
        for each in self.infos:
            if each['method'] != method:
                temp_infos.remove(each)
        return temp_infos

    def filter_teacher(self, teacher):
        temp_infos = self.infos[:]
        for each in self.infos:
            if each['situations'][0]['teacher'] != teacher:
                temp_infos.remove(each)
        return temp_infos

    def filter_group(self, group):
        temp_infos = self.infos[:]
        for each in self.infos:
            if (group[0] not in each['situations'][0]['groups']) or (group[1] not in each['situations'][0]['groups']):
                temp_infos.remove(each)
        return temp_infos

    def filter_subject(self, subject):
        temp_infos = self.infos[:]
        for each in self.infos:
            if each['info'][0]['name'] != subject:
                temp_infos.remove(each)
        return temp_infos


if __name__ == '__main__':
    CourseHandler()
