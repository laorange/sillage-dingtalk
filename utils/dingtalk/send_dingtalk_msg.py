from utils.dingtalk import dingTalkHandler
import asyncio


async def send_dingtalk_msg():
    userInfoTupleList = dingTalkHandler.getSillageUserAndUrlList()

    for userInfoTuple in userInfoTupleList:
        await dingTalkHandler.sendCorporationTextMsg([userInfoTuple[0].submitterUserId], userInfoTuple[1])


if __name__ == '__main__':
    asyncio.run(send_dingtalk_msg())
    breakpoint()
