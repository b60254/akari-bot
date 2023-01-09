import logging
import os
import re

from aiocqhttp import Event

from bots.aiocqhttp.client import bot
from bots.aiocqhttp.message import MessageSession, FetchTarget
from bots.aiocqhttp.message_guild import MessageSession as MessageSessionGuild
from config import Config
from core.elements import MsgInfo, Session, EnableDirtyWordCheck, PrivateAssets, Url
from core.parser.message import parser
from core.utils import init, load_prompt, init_async
from database import BotDBUtil

PrivateAssets.set(os.path.abspath(os.path.dirname(__file__) + '/assets'))
EnableDirtyWordCheck.status = Config('qq_enable_dirty_check')
Url.disable_mm = not Config('qq_enable_urlmanager')
init()
qq_account = Config("qq_account")


@bot.on_startup
async def startup():
    await init_async(FetchTarget)
    bot.logger.setLevel(logging.WARNING)


@bot.on_websocket_connection
async def _(event: Event):
    await load_prompt(FetchTarget)


@bot.on_message('group', 'private')
async def _(event: Event):
    if event.detail_type == 'private':
        if event.sub_type == 'group':
            return await bot.send(event, '请先添加好友后再进行命令交互。')
    filter_msg = re.match(r'.*?\[CQ:(?:json|xml).*?].*?|.*?<\?xml.*?>.*?', event.message)
    if filter_msg:
        return
    replyId = None
    match_reply = re.match(r'^\[CQ:reply,id=(.*?)].*', event.message)
    if match_reply:
        replyId = int(match_reply.group(1))

    prefix = None
    if match_at := re.match(r'^\[CQ:at,qq=(.*?)].*', event.message):
        if match_at.group(1) == qq_account:
            prefix = ['']

    targetId = 'QQ|' + (f'Group|{str(event.group_id)}' if event.detail_type == 'group' else str(event.user_id))

    msg = MessageSession(MsgInfo(targetId=targetId,
                                 senderId=f'QQ|{str(event.user_id)}',
                                 targetFrom='QQ|Group' if event.detail_type == 'group' else 'QQ',
                                 senderFrom='QQ', senderName='', clientName='QQ',
                                 messageId=event.message_id,
                                 replyId=replyId),
                         Session(message=event,
                                 target=event.group_id if event.detail_type == 'group' else event.user_id,
                                 sender=event.user_id))
    await parser(msg, running_mention=True, prefix=prefix)


class GuildAccountInfo:
    tiny_id = None


@bot.on_message('guild')
async def _(event):
    if GuildAccountInfo.tiny_id is None:
        profile = await bot.call_action('get_guild_service_profile')
        GuildAccountInfo.tiny_id = profile['tiny_id']
    tiny_id = event.user_id
    if tiny_id == GuildAccountInfo.tiny_id:
        return
    replyId = None
    match_reply = re.match(r'^\[CQ:reply,id=(.*?)].*', event.message)
    if match_reply:
        replyId = int(match_reply.group(1))
    targetId = f'QQ|Guild|{str(event.guild_id)}|{str(event.channel_id)}'
    msg = MessageSessionGuild(MsgInfo(targetId=targetId,
                                      senderId=f'QQ|Tiny|{str(event.user_id)}',
                                      targetFrom='QQ|Guild',
                                      senderFrom='QQ|Tiny', senderName='', clientName='QQ', messageId=event.message_id,
                                      replyId=replyId),
                              Session(message=event,
                                      target=f'{str(event.guild_id)}|{str(event.channel_id)}',
                                      sender=event.user_id))
    await parser(msg, running_mention=True)


"""@bot.on('request.friend')
async def _(event: Event):
    if BotDBUtil.SenderInfo('QQ|' + str(event.user_id)).query.isInBlockList:
        return {'approve': False}
    return {'approve': True}"""


@bot.on('request.group.invite')
async def _(event: Event):
    await bot.send_private_msg(user_id=event.user_id,
                               message='你好！本机器人暂时不主动同意入群请求。\n'
                                       '请至https://github.com/Teahouse-Studios/bot/issues/new?assignees=OasisAkari&labels=New&template=add_new_group.yaml&title=%5BNEW%5D%3A+申请入群。')


@bot.on_notice('group_ban')
async def _(event: Event):
    if event.user_id == int(qq_account):
        result = BotDBUtil.UnfriendlyActions(targetId=event.group_id,
                                             senderId=event.operator_id).add_and_check('mute', str(event.duration))
        if event.duration >= 259200:
            result = True
        if result:
            await bot.call_action('set_group_leave', group_id=event.group_id)
            BotDBUtil.SenderInfo('QQ|' + str(event.operator_id)).edit('isInBlockList', True)
            await bot.call_action('delete_friend', friend_id=event.operator_id)


"""
@bot.on_message('group')
async def _(event: Event):
    result = BotDBUtil.isGroupInAllowList(f'QQ|Group|{str(event.group_id)}')
    if not result:
        await bot.send(event=event, message='此群不在白名单中，已自动退群。'
                                            '\n如需申请白名单，请至https://github.com/Teahouse-Studios/bot/issues/new/choose发起issue。')
        await bot.call_action('set_group_leave', group_id=event.group_id)
"""

qq_host = Config("qq_host")
if qq_host:
    host, port = qq_host.split(':')
    bot.run(host=host, port=port, debug=False)
