from typing import TypedDict, List, Dict, Literal, Tuple, Optional
from pydantic import BaseModel

UserId = str
UserName = str
UnionId = str
DepartmentId = int
DepartmentName = str
Method = Literal["GET", "POST"]

UserNameIdDict = Dict[UserName, UserId]

UserNameIdTuple = Tuple[UserName, UserId]


class UserInfoDict(TypedDict):
    name: UserName
    userid: UserId


class DepartmentDict(TypedDict):
    ext: str  # --------------------------- "ext": "{\"faceCount\":\"int\"}",
    auto_add_user: bool  # ---------------- "auto_add_user": true,
    parent_id: int  # --------------------- "parent_id": 1,
    name: DepartmentName  # --------------- "name": "xx部门",
    dept_id: DepartmentId  # -------------- "dept_id": int,
    create_dept_group: bool  # ------------ "create_dept_group": true


class AdministratorInfo(TypedDict):
    sys_level: Literal[1, 2]
    userid: UserId


class UserDetail(TypedDict):
    userid: str
    unionid: str
    name: str
    job_number: str
    title: str
    exclusive_account: str
    dept_id_list: List[int]
    hired_date: int
    real_authed: bool
    active: bool
    admin: bool
    senior: bool
    boss: str
    manager_userid: str


class DeptAddressBook(TypedDict):
    dept_id: DepartmentId
    dept_name: str
    users: List[UserDetail]


AddressBook = List[DeptAddressBook]


class Settings(TypedDict):
    AGENT_ID: str
    APP_KEY: str
    APP_SECRET: str
    STATUS: Literal["INIT", "PREPARED", "WORKING", "DONE"]
    ADDRESS_BOOK: AddressBook


# form
class FormProfile(BaseModel):
    #     {
    #         "creator":"\d+",
    #         "formCode":"\w+",
    #         "name":"订阅钉钉推送",
    #         "memo":"您可以通过填写此表来订阅每天的课程提醒",
    #         "setting":{
    #             "formType":0,
    #             "bizType":0,
    #             "stop":false,
    #             "createTime":"2022-08-11T10:22Z"
    #         }
    #     }[]
    formCode: str
    creator: str
    name: str
    memo: str


class FormDetail(BaseModel):
    label: Optional[str]
    key: Optional[str]
    value: str


class FormRecord(BaseModel):
    forms: List[FormDetail]
    createTime: str
    modifyTime: str
    formCode: str
    submitterUserId: str
    submitterUserName: Optional[str]
    formInstanceId: str


class FormResult(BaseModel):
    hasMore: bool
    nextToken: str
    list: Optional[List[FormRecord]]
