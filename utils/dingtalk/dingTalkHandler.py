import json
import datetime

import httpx
from tqdm import tqdm
import asyncio

from utils.dingtalk.types import *


def getSettings(settingFileName) -> Settings:
    import json
    _settings = dict()
    try:
        with open(settingFileName, encoding="utf-8") as settings_json:
            print(f"\nTIPS：已自动加载缓存。若需重新输入密钥等敏感信息，请删除配置文件”{settingFileName}“\n")
            _settings = json.load(settings_json)
    finally:
        return _settings


def outputSettings(settings: Settings, settingFileName):
    with open(settingFileName, "wt", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False)


class DingTalkHandler:
    def __init__(self, settingFileName: str = "settings.json"):
        self.settingFileName = settingFileName
        settings = getSettings(settingFileName)
        # 权限
        self.agentId: str = _ if (_ := settings.get("AGENT_ID", None)) else input("请输入AgentId: ")
        self.appKey: str = _ if (_ := settings.get("APP_KEY", None)) else input("请输入AppKey: ")
        self.appSecret: str = _ if (_ := settings.get("APP_SECRET", None)) else input("请输入AppSecret: ")
        assert self.agentId and self.appKey and self.appSecret

        self.accessToken: str = self.getAccessToken()

        self.status = settings.get("STATUS", "INIT")

        if self.status == "DONE":
            self.addressBook: AddressBook = settings.get("ADDRESS_BOOK", {})
        else:
            asyncio.run(self.refreshAddressBook())

    async def refreshAddressBook(self):
        self.addressBook = await self.getAddressBook()
        outputSettings({"AGENT_ID": self.agentId,
                        "APP_KEY": self.appKey,
                        "APP_SECRET": self.appSecret,
                        "STATUS": self.status,
                        "ADDRESS_BOOK": self.addressBook}, self.settingFileName)

    def getAccessToken(self) -> str:
        url = "https://oapi.dingtalk.com/gettoken"
        params = dict(appkey=self.appKey, appsecret=self.appSecret)
        try:
            accessToken = httpx.get(url, params=params).json()["access_token"]
        except Exception as e:
            print(f"ERROR：验证密钥失败，请检查应用凭证是否正确，或检查网络连接。({e})")
            raise e
        self.status = "PREPARED"
        self.accessToken = accessToken
        return accessToken

    def refreshAccessToken(self):
        self.accessToken = self.getAccessToken()

    @staticmethod
    async def getDingTalkResponse(method: Method, url: str, **kwargs) -> Dict:
        if method == "GET":
            async with httpx.AsyncClient() as client:
                response = (await client.get(url, **kwargs)).json()
        elif method == "POST":
            async with httpx.AsyncClient() as client:
                response = (await client.post(url, **kwargs)).json()
        else:
            raise Exception("暂不支持别的请求方式")
        if response.get("errcode", -1) != 0:
            raise Exception(response.get("errmsg", str(response)))
        return response

    async def getSubDepartmentIdList(self, departmentId: DepartmentId = 1) -> List[DepartmentId]:
        url = "https://oapi.dingtalk.com/topapi/v2/department/listsubid"
        params = dict(access_token=self.accessToken)
        data = dict(dept_id=departmentId)
        response = await self.getDingTalkResponse("POST", url=url, params=params, json=data)
        return response["result"]["dept_id_list"]

    async def getDescendantDepartmentIdList(self, departmentId: DepartmentId = 1) -> List[DepartmentId]:
        descendantDepartmentIdList = await self.getSubDepartmentIdList(departmentId)
        if len(descendantDepartmentIdList) != 0:
            for descendantDepartmentId in tqdm(descendantDepartmentIdList, desc="正在获取部门信息"):
                descendantDepartmentIdList += await self.getSubDepartmentIdList(descendantDepartmentId)
        return descendantDepartmentIdList + [1]  # 根部门 id=1

    async def getSimpleUserList(self, dept_id: DepartmentId = 1, cursor=0, size=100) -> List[UserInfoDict]:
        url = "https://oapi.dingtalk.com/topapi/user/listsimple"
        params = dict(access_token=self.accessToken)
        data = dict(dept_id=dept_id, cursor=cursor, size=size)
        response = await self.getDingTalkResponse("POST", url, params=params, json=data)
        userList: List[UserInfoDict] = response["result"]["list"]

        if response["result"]["has_more"]:
            userList = userList + (await self.getSimpleUserList(dept_id=dept_id, cursor=cursor + 1, size=size))

        return userList

    async def getUserDetail(self, userId: UserId) -> UserDetail:
        url = "https://oapi.dingtalk.com/topapi/v2/user/get"
        params = dict(access_token=self.accessToken)
        data = dict(userid=userId)
        response = await self.getDingTalkResponse("POST", url, params=params, json=data)
        return response["result"]

    async def getUserDetailListOfDepartment(self, dept_id: DepartmentId = 1) -> List[UserDetail]:
        simpleUserList = await self.getSimpleUserList(dept_id)

        # return [await self.getUserDetail(simpleUser["userid"]) for simpleUser in simpleUserList]

        # # 不可行：会请求到钉钉限流
        # userDetailListOfDepartment: List[UserDetail] = []
        # for f in asyncio.as_completed([self.getUserDetail(simpleUser["userid"]) for simpleUser in simpleUserList]):
        #     userDetailListOfDepartment.append(await f)
        # return userDetailListOfDepartment

        return [(await self.getUserDetail(simpleUser["userid"])) for simpleUser in simpleUserList]

    async def getDepartmentName(self, departmentId: DepartmentId = 1) -> DepartmentName:
        url = "https://oapi.dingtalk.com/topapi/v2/department/get"
        params = dict(access_token=self.accessToken)
        data = dict(dept_id=departmentId)
        response = await self.getDingTalkResponse("POST", url, params=params, json=data)
        return response["result"]["name"]

    async def getDeptAddressBook(self, dept_id: DepartmentId = 1) -> DeptAddressBook:
        return {"dept_id": dept_id, "dept_name": await self.getDepartmentName(dept_id), "users": await self.getUserDetailListOfDepartment(dept_id)}

    async def getAddressBook(self) -> AddressBook:
        self.status = "WORKING"
        departmentIdList = await self.getDescendantDepartmentIdList()
        addressBook = [(await self.getDeptAddressBook(departmentId)) for departmentId in tqdm(departmentIdList, desc="正在获取部门成员信息")]
        self.status = "DONE"
        return addressBook

    async def getUnionIdOfUserId(self, userId: str) -> str:
        userDetail = await self.getUserDetail(userId)
        return userDetail["unionid"]

    async def sendBulletin(self, data) -> Dict:
        url = "https://oapi.dingtalk.com/topapi/blackboard/create"
        params = dict(access_token=self.accessToken)

        # private_level = 20 if whether_private else 0
        # data = {"create_request": {
        #     "operation_userid": self.publisher[1],
        #     "private_level": private_level,
        #     "ding": whether_ding,
        #     "blackboard_receiver": {
        #         "userid_list": user_id_list
        #     },
        #     "title": title,
        #     "content": content,
        #     "push_top": whether_push_top,
        #     "author": self.publisher[0]
        # }}

        return await self.getDingTalkResponse("POST", url, params=params, json=data)

    async def sendTextBulletin(self, operation_userid: str, user_id_list: List[UserId], title: str, content: str,
                               author: str = "辣橙", is_private: bool = True, use_ding: bool = True, push_top: bool = False):
        """ 限制：operation_userid对应人员需要具有公告发布权限 """
        private_level = 20 if is_private else 0
        bulletin_data = {"create_request": {
            "operation_userid": operation_userid,
            "private_level": private_level,
            "ding": use_ding,
            "blackboard_receiver": {
                "userid_list": user_id_list
            },
            "title": title,
            "content": content,
            "push_top": push_top,
            "author": author
        }}
        await self.sendBulletin(bulletin_data)
        await asyncio.sleep(1)

    async def sendCorporationMsg(self, user_id_list: List[UserId], msg: Dict) -> Dict:
        """
        发送工作消息\n
        :param user_id_list: 发送目标的id
        :param msg: 发送的消息内容
        :return: post请求后的结果
        """
        url = "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"
        params = dict(access_token=self.accessToken)
        data = {"agent_id": self.agentId,
                "msg": msg,
                "userid_list": ",".join(user_id_list)}

        return await self.getDingTalkResponse("POST", url, params=params, json=data)

    async def sendCorporationTextMsg(self, user_id_list: List[UserId], text: str) -> Dict:
        """发送文字类型的工作消息"""
        return await self.sendCorporationMsg(user_id_list, msg={"msgtype": "text", "text": {"content": text}})

    async def sendCorporationMarkdownMsg(self, user_id_list: List[UserId], title: str, text: str) -> Dict:
        """发送Markdown类型的工作消息"""
        return await self.sendCorporationMsg(user_id_list, msg={"msgtype": "markdown", "markdown": {"title": title, "text": text}})

    async def createCalendar(self, title: str, content: str, attendeesUnionIdList: List[str],
                             start_time: datetime.datetime, end_time: datetime.datetime, remindMin: int = 0):
        senderUnionId = attendeesUnionIdList[0]  # 将第一位与会者设为发起人
        url = f"https://api.dingtalk.com/v1.0/calendar/users/{senderUnionId}/calendars/primary/events"
        data = {
            "summary": title,
            "description": content,
            "isAllDay": False,
            "start": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "timeZone": "Asia/Shanghai",
            },
            "end": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "timeZone": "Asia/Shanghai",
            },
            "reminders": [{"method": "dingtalk", "minutes": remindMin}] if remindMin else [],
            "attendees": [{"id": attendeesUnionId, "isOptional": False} for attendeesUnionId in attendeesUnionIdList],
        }
        response = httpx.post(url, json=data, headers={"x-acs-dingtalk-access-token": self.accessToken})
        return response

    def getForms(self) -> List[FormProfile]:
        url = f"https://api.dingtalk.com/v1.0/swform/users/forms"
        headers = {"x-acs-dingtalk-access-token": self.accessToken}
        params = dict(maxResults=200, bizType=0, nextToken=0)

        rawForms = httpx.get(url, headers=headers, params=params).json()["result"]["list"]
        return [FormProfile(**rawForm) for rawForm in rawForms]

    def getFormRecords(self, formCode: str) -> List[FormRecord]:
        url = f"https://api.dingtalk.com/v1.0/swform/forms/{formCode}/instances"
        headers = {"x-acs-dingtalk-access-token": self.accessToken}
        params = dict(maxResults=100, bizType=0, nextToken=0)
        response: dict = httpx.get(url, headers=headers, params=params).json()

        rawFormResult = response.get("result", {"hasMore": False, "nextToken": 10, "list": []})
        formResult = FormResult(**rawFormResult)
        forms = formResult.list

        while formResult.hasMore:
            params = dict(maxResults=100, bizType=0, nextToken=formResult.nextToken)
            response = httpx.get(url, headers=headers, params=params).json()
            rawFormResult = response.get("result", {"hasMore": False, "nextToken": 10, "list": []})
            formResult = FormResult(**rawFormResult)
            forms += formResult.list

        return forms

    def getSillageUserAndUrlList(self) -> List[Tuple[FormRecord, str]]:
        outputs: List[Tuple[FormRecord, str]] = []

        forms = self.getForms()
        formRecords = self.getFormRecords(forms[0].formCode)
        for formRecord in formRecords:
            # 查找 是否启用钉钉推送
            if len([formDetail for formDetail in formRecord.forms if (formDetail.label == '是否启用钉钉推送？' and formDetail.value == '启用')]):
                # 查找 用户订阅的链接
                urls = [formDetail.value for formDetail in formRecord.forms if formDetail.label == '请输入您要订阅的课表网址：']
                if not len(urls):
                    raise Exception("表单内容已变更，请检查！")
                url: str = urls[0]
                outputs.append((formRecord, url))

        return outputs
