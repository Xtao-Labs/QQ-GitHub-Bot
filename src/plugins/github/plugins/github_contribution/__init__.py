"""
@Author         : yanyongyu
@Date           : 2024-05-30 17:30:18
@LastEditors    : yanyongyu
@LastEditTime   : 2024-05-31 15:40:54
@Description    : None
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

from datetime import date

from nonebot import logger, on_command
from nonebot.plugin import PluginMetadata
from playwright.async_api import Error, TimeoutError
from nonebot.adapters.onebot.v11 import MessageSegment as QQMS
from nonebot.adapters.qq import MessageSegment as QQOfficialMS
from nonebot.adapters.github import ActionFailed, GraphQLError, ActionTimeout

from src.plugins.github import config
from src.plugins.github.utils import get_github_bot
from src.plugins.github.helpers import NO_GITHUB_EVENT
from src.providers.platform import TARGET_INFO, TargetType
from src.plugins.github.dependencies import AUTHORIZED_USER
from src.plugins.github.libs.renderer import user_contribution_to_image

__plugin_meta__ = PluginMetadata(
    "GitHub 贡献查询", "查询 GitHub 贡献", "/contribution: 查看个人贡献"
)


CONTRIBUTION_QUERY: str = """
query {
  viewer {
    login
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionLevel
            date
          }
        }
      }
    }
  }
}
"""


contribution = on_command(
    "contribution",
    aliases={"contribute", "contri", "贡献", "贡献查询", "tile"},
    rule=NO_GITHUB_EVENT,
    priority=config.github_command_priority,
)


@contribution.handle()
async def handle_contribution(
    target_info: TARGET_INFO,
    user: AUTHORIZED_USER,
):
    bot = get_github_bot()

    try:
        async with bot.as_user(user.access_token):
            resp = await bot.async_graphql(query=CONTRIBUTION_QUERY)
    except ActionTimeout:
        await contribution.finish("GitHub API 超时，请稍后再试")
    except ActionFailed as e:
        logger.opt(exception=e).error(f"Failed while get user contribution: {e}")
        await contribution.finish("未知错误发生，请尝试重试或联系管理员")
    except GraphQLError as e:
        logger.opt(exception=e).error(f"Failed while get user contribution: {e}")
        await contribution.finish("未知错误发生，请尝试重试或联系管理员")
    except Exception as e:
        logger.opt(exception=e).error(f"Failed while get user contribution: {e}")
        await contribution.finish("未知错误发生，请尝试重试或联系管理员")

    username = resp["viewer"]["login"]
    calendar = resp["viewer"]["contributionsCollection"]["contributionCalendar"]
    total_contributions: int = calendar["totalContributions"]
    weeks: list[list[tuple[str, date]]] = [
        [
            (day["contributionLevel"], date.fromisoformat(day["date"]))
            for day in week["contributionDays"]
        ]
        for week in calendar["weeks"]
    ]

    try:
        img = await user_contribution_to_image(username, total_contributions, weeks)
    except ActionTimeout:
        await contribution.finish("GitHub API 超时，请稍后再试")
    except TimeoutError:
        await contribution.finish("生成图片超时！请稍后再试")
    except Error:
        await contribution.finish("生成图片出错！请稍后再试")
    except Exception as e:
        logger.opt(exception=e).error(
            f"Failed while generating contribution image: {e}"
        )
        await contribution.finish("生成图片出错！请稍后再试")

    match target_info.type:
        case TargetType.QQ_USER | TargetType.QQ_GROUP:
            await contribution.send(QQMS.image(img))
        case TargetType.QQ_OFFICIAL_USER | TargetType.QQ_OFFICIAL_GROUP:
            await contribution.send(QQOfficialMS.file_image(img))
        case TargetType.QQGUILD_USER | TargetType.QQGUILD_CHANNEL:
            await contribution.send(QQOfficialMS.file_image(img))
