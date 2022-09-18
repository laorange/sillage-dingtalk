from typing import Optional, List, Union

from pydantic import BaseModel


class PocketBaseModel(BaseModel):
    id: str
    created: Optional[str]
    updated: Optional[str]


class Situation(BaseModel):
    # teacher: Optional[str]
    # room: Optional[str]
    groups: Optional[List[str]]
    teachers: Optional[List[str]]
    rooms: Optional[List[str]]


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


class QueryParseResult(BaseModel):
    grade: Optional[List[str]]
    room: Optional[List[str]]
    method: Optional[List[str]]
    teacher: Optional[List[str]]
    group: Optional[List[str]]
    subject: Optional[List[str]]
