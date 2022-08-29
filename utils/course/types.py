from typing import Optional, List

from pydantic import BaseModel


class PocketBaseModel(BaseModel):
    id: str
    created: Optional[str]
    updated: Optional[str]


class Situation(BaseModel):
    teacher: Optional[str]
    room: Optional[str]
    groups: Optional[List[str]]


class CourseInfo(BaseModel):
    name: str
    code: Optional[str]
    bgc: str


class Course(PocketBaseModel):
    info: CourseInfo
    situations: List[Situation]
    grade: str

    dates: List[str]
    lessonNum: int

    note: Optional[str]
    method: Optional[str]

