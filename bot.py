"""
개인 서버 전담 관리 AI 디스코드 봇 (AI Discord Butler)
- 모델: Google Gemini 2.5 Flash (google-genai SDK)
- 디스코드 라이브러리: discord.py (Intents.all() 활성화)
- 배포 플랫폼: Render.com 무료 웹 서비스 (aiohttp 백그라운드 서버 포트 바인딩 지원)
"""

import os
import sys
import json
import logging
import urllib.parse
import asyncio
from typing import Dict, Any

# 로컬 환경에서 .env 파일이 존재하는 경우 자동 로드 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import discord
from discord.ext import commands
from aiohttp import web
from google import genai
from google.genai import types

# ==============================================================================
# 1. 로깅 및 환경 변수 검증
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DiscordButler")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.getenv("PORT", "8080"))
MODEL_NAME = "gemini-2.5-flash"

# 필수 환경 변수 누락 시 안내 후 안전하게 종료
missing_vars = []
if not DISCORD_TOKEN:
    missing_vars.append("DISCORD_TOKEN")
if not GEMINI_API_KEY:
    missing_vars.append("GEMINI_API_KEY")

if missing_vars:
    print("\n" + "=" * 65)
    print(" [치명적 오류] 필수 환경 변수가 누락되었습니다!")
    print(f" 누락된 항목: {', '.join(missing_vars)}")
    print("\n [해결 가이드]")
    print(" 1. 로컬 환경:")
    print("    .env 파일을 프로젝트 루트에 생성하고 아래와 같이 채워주세요:")
    print("    DISCORD_TOKEN=디스코드_봇_토큰_입력")
    print("    GEMINI_API_KEY=구글_제미나이_API키_입력")
    print("    PORT=8080")
    print(" 2. Render.com 배포 환경:")
    print("    대시보드 > Environment > Environment Variables 에서 등록해주세요.")
    print("=" * 65 + "\n")
    sys.exit(1)

# Gemini 클라이언트 초기화
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# ==============================================================================
# 2. Gemini 도구(Function Calling) 정의 및 도구 스키마
# ==============================================================================
create_channel_func = types.FunctionDeclaration(
    name="create_channel",
    description="디스코드 서버에 새로운 텍스트 채널 또는 음성 채널을 생성합니다.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "생성할 채널의 이름 (예: 공지사항, 수다방 등)",
            },
            "channel_type": {
                "type": "string",
                "enum": ["text", "voice"],
                "description": "채널 종류. 'text'(텍스트 채널) 또는 'voice'(음성 채널). 기본값은 'text'.",
            },
        },
        "required": ["name"],
    },
)

delete_channel_func = types.FunctionDeclaration(
    name="delete_channel",
    description="디스코드 서버에서 특정 채널을 삭제하거나 현재 메시지가 입력된 채널을 삭제합니다.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "삭제할 채널 이름. 현재 채널을 삭제하려는 경우 'current' 또는 '현재'를 입력하세요.",
            },
        },
        "required": ["name"],
    },
)

create_role_func = types.FunctionDeclaration(
    name="create_role",
    description="디스코드 서버에 새로운 역할을 생성합니다.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "생성할 역할의 이름 (예: 관리자, VIP, 손님 등)",
            },
        },
        "required": ["name"],
    },
)

purge_messages_func = types.FunctionDeclaration(
    name="purge_messages",
    description="현재 채널에서 최근 메시지들을 일괄 삭제(청소)합니다. (최대 100개)",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "amount": {
                "type": "integer",
                "description": "삭제할 메시지 개수 (1 이상 100 이하 정수)",
            },
        },
        "required": ["amount"],
    },
)

invite_bot_link_func = types.FunctionDeclaration(
    name="invite_bot_link",
    description="다른 디스코드 봇(예: 음악봇, 게임봇 등)을 초대할 수 있는 안내 및 Top.gg 검색 링크를 제공합니다.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "bot_name": {
                "type": "string",
                "description": "검색하거나 초대하려는 봇의 이름 (예: 리듬, 아야나, 하이드라 등)",
            },
        },
        "required": ["bot_name"],
    },
)

GEMINI_TOOLS = [
    types.Tool(
        function_declarations=[
            create_channel_func,
            delete_channel_func,
            create_role_func,
            purge_messages_func,
            invite_bot_link_func,
        ]
    )
]

SYSTEM_INSTRUCTION = """
너는 디스코드 개인 서버의 전담 관리자이자 충직하고 유능한 AI 집사(Butler)이다.
사용자의 자연어 명령을 분석하여 서버 관리 작업을 신속하고 정중하게 처리한다.

[행동 원칙]
1. 사용자가 채널 생성/삭제, 역할 생성, 메시지 청소, 봇 초대 링크 요청을 하면 제공된 관리 도구(Tool)를 적절히 호출하라.
2. 도구 실행 결과가 주어지면, 사용자의 품격에 맞춰 정중하고 명확한 경어체('~하였습니다', '~하겠습니다', '~드리겠습니다')로 결과를 보고하라.
3. 도구 호출이 필요 없는 일반 대화, 질문, 서버 운영 상담 등에는 유식하고 친절한 AI 집사의 페르소나를 유지하며 자연스럽게 대답하라.
4. 사용자가 특정 채널 삭제를 명시하지 않고 "이 채널", "현재 채널" 등의 표현을 쓰면 delete_channel의 name 인자에 "current"를 전달하라.
5. 한국어로 자연스럽고 깔끔하게 답변하라.
"""

# ==============================================================================
# 3. 디스코드 관리 도구 실제 구현 함수
# ==============================================================================
async def tool_create_channel(guild: discord.Guild, channel_type: str, name: str, current_channel: discord.abc.GuildChannel) -> str:
    """새로운 텍스트 또는 음성 채널 생성"""
    if not guild:
        return "오류: 채널 생성 명령은 서버(길드) 채널 내에서만 실행할 수 있습니다."
    if not guild.me.guild_permissions.manage_channels:
        return "권한 부족: 봇에게 '채널 관리(Manage Channels)' 권한이 없습니다. 서버 설정에서 권한을 부여해 주세요."

    c_type = (channel_type or "text").lower().strip()
    category = getattr(current_channel, "category", None)

    try:
        if c_type in ["voice", "음성", "음성채널"]:
            new_ch = await guild.create_voice_channel(name=name, category=category, reason="AI 집사 명령에 따른 음성 채널 생성")
            return f"성공: 음성 채널 '{new_ch.name}'이(가) 성공적으로 생성되었습니다. (ID: {new_ch.id})"
        else:
            new_ch = await guild.create_text_channel(name=name, category=category, reason="AI 집사 명령에 따른 텍스트 채널 생성")
            return f"성공: 텍스트 채널 '{new_ch.name}'이(가) 성공적으로 생성되었습니다. (ID: {new_ch.id})"
    except discord.Forbidden:
        return "권한 부족: 디스코드 권한 제약으로 채널을 생성하지 못했습니다."
    except Exception as e:
        logger.error(f"create_channel error: {e}")
        return f"실패: 채널 생성 중 오류 발생 ({e})"


async def tool_delete_channel(guild: discord.Guild, name: str, current_channel: discord.abc.GuildChannel, author: discord.Member) -> str:
    """채널 삭제 (특정 채널 또는 현재 채널)"""
    if not guild:
        return "오류: 채널 삭제 명령은 서버(길드) 채널 내에서만 실행할 수 있습니다."
    if not guild.me.guild_permissions.manage_channels:
        return "권한 부족: 봇에게 '채널 관리(Manage Channels)' 권한이 없습니다."

    name_lower = (name or "").strip().lower()
    target_channel = None

    # '현재', '이 채널', 'current' 또는 현재 채널 이름과 일치하는 경우
    if name_lower in ["current", "현재", "이 채널", "현재 채널", "this", "this channel", ""] or (hasattr(current_channel, "name") and name_lower == current_channel.name.lower()):
        target_channel = current_channel
    else:
        clean_name = name.lstrip("#").strip().lower()
        target_channel = discord.utils.find(
            lambda c: c.name.lower() == clean_name,
            guild.channels
        )

    if not target_channel:
        return f"실패: '{name}' 이름의 채널을 서버에서 찾을 수 없습니다. 정확한 채널명을 확인해 주세요."

    ch_name = target_channel.name
    try:
        # 현재 채널을 삭제하는 경우 채널 삭제 전 알림 및 DM 발송 시도
        if target_channel == current_channel:
            try:
                await current_channel.send(f"⚠️ 요청에 따라 **#{ch_name}** 채널을 즉시 삭제합니다...")
            except Exception:
                pass
            try:
                await author.send(f"[{guild.name}] 서버의 '#{ch_name}' 채널 삭제 작업이 완료되었습니다.")
            except Exception:
                pass
            await target_channel.delete(reason="AI 집사 명령에 따른 현재 채널 삭제")
            return f"성공: 현재 채널 '#{ch_name}'이(가) 성공적으로 삭제되었습니다."
        else:
            await target_channel.delete(reason="AI 집사 명령에 따른 채널 삭제")
            return f"성공: '#{ch_name}' 채널이 성공적으로 삭제되었습니다."
    except discord.Forbidden:
        return "권한 부족: 디스코드 권한 제약으로 채널을 삭제하지 못했습니다."
    except Exception as e:
        logger.error(f"delete_channel error: {e}")
        return f"실패: 채널 삭제 중 오류 발생 ({e})"


async def tool_create_role(guild: discord.Guild, name: str) -> str:
    """새로운 역할 생성"""
    if not guild:
        return "오류: 역할 생성 명령은 서버(길드) 채널 내에서만 실행할 수 있습니다."
    if not guild.me.guild_permissions.manage_roles:
        return "권한 부족: 봇에게 '역할 관리(Manage Roles)' 권한이 없습니다. 서버 설정에서 권한을 부여해 주세요."

    try:
        existing = discord.utils.get(guild.roles, name=name)
        if existing:
            return f"안내: '{name}' 역할이 이미 서버에 존재합니다. (역할 ID: {existing.id})"

        new_role = await guild.create_role(name=name, reason="AI 집사 명령에 따른 신규 역할 생성")
        return f"성공: '{new_role.name}' 역할이 성공적으로 생성되었습니다. (역할 ID: {new_role.id})"
    except discord.Forbidden:
        return "권한 부족: 디스코드 권한 제약으로 역할을 생성하지 못했습니다."
    except Exception as e:
        logger.error(f"create_role error: {e}")
        return f"실패: 역할 생성 중 오류 발생 ({e})"


async def tool_purge_messages(channel: discord.abc.Messageable, guild: discord.Guild, amount: int) -> str:
    """현재 채널 메시지 일괄 청소"""
    if not guild or not hasattr(channel, "purge"):
        return "오류: 메시지 청소 명령은 서버(길드) 텍스트 채널 내에서만 실행할 수 있습니다."
    if not channel.permissions_for(guild.me).manage_messages:
        return "권한 부족: 봇에게 이 채널의 '메시지 관리(Manage Messages)' 권한이 없습니다."

    try:
        count = max(1, min(100, int(amount)))
        # 사용자의 명령 메시지를 포함하여 삭제하기 위해 +1
        deleted = await channel.purge(limit=count + 1)
        actual_deleted = max(0, len(deleted) - 1)
        return f"성공: 현재 채널에서 최근 메시지 {actual_deleted}개를 깨끗하게 청소(삭제)했습니다."
    except discord.Forbidden:
        return "권한 부족: 메시지 관리 권한이 부족하여 삭제하지 못했습니다."
    except discord.HTTPException as e:
        if "14 days" in str(e).lower():
            return "안내: 디스코드 정책상 14일이 지난 메시지는 일괄 삭제할 수 없습니다. 14일 이내의 메시지만 청소되었습니다."
        return f"실패: 메시지 청소 중 오류 발생 ({e})"
    except Exception as e:
        logger.error(f"purge_messages error: {e}")
        return f"실패: 메시지 청소 중 오류 발생 ({e})"


def tool_invite_bot_link(bot_name: str) -> str:
    """다른 봇 초대 링크 및 보안 정책 안내"""
    clean_name = (bot_name or "디스코드봇").strip()
    encoded = urllib.parse.quote(clean_name)
    topgg_url = f"https://top.gg/search?q={encoded}"

    return (
        f"디스코드 보안 정책상 어떤 봇도 다른 봇을 서버에 임의로 강제 초대/추가할 수는 없습니다.\n"
        f"서버 관리 권한을 가진 사용자가 공식 OAuth2 링크를 통해 직접 승인해 주셔야 합니다.\n\n"
        f"요청하신 **{clean_name}** 봇의 공식 초대 링크는 아래 Top.gg 검색을 통해 바로 확인하실 수 있습니다:\n"
        f"👉 [Top.gg에서 '{clean_name}' 검색 및 초대 링크 바로가기]({topgg_url})"
    )


async def execute_tool_dispatch(func_name: str, args: Dict[str, Any], message: discord.Message) -> str:
    """함수명에 따라 적절한 도구 로직을 비동기로 실행"""
    guild = message.guild
    channel = message.channel

    if func_name == "create_channel":
        name = args.get("name", "새-채널")
        channel_type = args.get("channel_type", "text")
        return await tool_create_channel(guild, channel_type, name, channel)

    elif func_name == "delete_channel":
        name = args.get("name", "current")
        return await tool_delete_channel(guild, name, channel, message.author)

    elif func_name == "create_role":
        name = args.get("name", "새-역할")
        return await tool_create_role(guild, name)

    elif func_name == "purge_messages":
        amount = args.get("amount", 10)
        return await tool_purge_messages(channel, guild, amount)

    elif func_name == "invite_bot_link":
        bot_name = args.get("bot_name", "")
        return tool_invite_bot_link(bot_name)

    else:
        return f"오류: 알 수 없는 관리 도구 '{func_name}'입니다."


# ==============================================================================
# 4. 디스코드 봇 클라이언트 설정 및 이벤트
# ==============================================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


async def send_safely(message: discord.Message, text: str):
    """디스코드 2000자 제한을 안전하게 분할하여 회신 (원본 메시지 삭제 시 채널 전송 대체)"""
    if not text:
        text = "요청하신 작업을 성공적으로 마쳤습니다."

    max_len = 1900
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]

    for idx, chunk in enumerate(chunks):
        try:
            if idx == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(chunk)
        except (discord.NotFound, discord.HTTPException):
            try:
                await message.channel.send(chunk)
            except discord.HTTPException:
                pass


@bot.event
async def on_ready():
    logger.info("=" * 50)
    logger.info(f"✨ AI 관리자 디스코드 봇 로그인 완료: {bot.user.name}#{bot.user.discriminator} (ID: {bot.user.id})")
    logger.info(f"✨ 연결된 서버 수: {len(bot.guilds)}개")
    for g in bot.guilds:
        logger.info(f"   - {g.name} (ID: {g.id})")
    logger.info("=" * 50)
    await bot.change_presence(activity=discord.Game(name="!도움말 | 개인 서버 관리 비서"))


@bot.event
async def on_message(message: discord.Message):
    # 봇 자신의 메시지 및 다른 봇 메시지 무시
    if message.author.bot:
        return

    # 트리거 조건 확인: DM, 멘션(@봇), 느낌표(!) 접두사
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions if bot.user else False
    is_prefix = message.content.startswith("!")

    if not (is_dm or is_mentioned or is_prefix):
        return

    # 순수 프롬프트 텍스트 추출
    prompt = message.content
    if is_prefix:
        prompt = prompt[1:].strip()
    if is_mentioned and bot.user:
        prompt = prompt.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()

    if not prompt:
        greeting = (
            f"주인님, 부르셨습니까? 무엇을 도와드릴까요?\n\n"
            f"**사용 가능한 예시:**\n"
            f"• `!공지사항 텍스트 채널 만들어줘`\n"
            f"• `!수다방 음성 채널 만들어줘`\n"
            f"• `!채팅 30개 청소해줘`\n"
            f"• `!VIP 역할 추가해줘`\n"
            f"• `!음악봇 데려와`\n"
            f"• `!이 채널 삭제해`"
        )
        await send_safely(message, greeting)
        return

    # 디스코드 입력 중(typing) 표시 활성화
    try:
        async with message.channel.typing():
            await process_gemini_request(message, prompt)
    except Exception as e:
        logger.error(f"메시지 처리 중 예외 발생: {e}")
        await send_safely(message, f"요청을 처리하는 도중 예기치 못한 문제가 발생했습니다: {e}")


async def process_gemini_request(message: discord.Message, prompt: str):
    """Gemini 2.5 Flash와 통신하여 Function Calling 및 자연어 응답 처리"""
    try:
        # 1. 1차 Gemini 호출
        response = await gemini_client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=GEMINI_TOOLS,
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            ),
        )

        # 2. 도구(Function Calling) 호출 여부 확인
        if response.function_calls:
            tool_results = []
            tool_response_parts = []

            for call in response.function_calls:
                func_name = call.name
                func_args = dict(call.args) if call.args else {}
                logger.info(f"🔧 도구 호출 감지: {func_name} (인자: {func_args})")

                result_text = await execute_tool_dispatch(func_name, func_args, message)
                tool_results.append(result_text)

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=func_name,
                        response={"result": result_text},
                    )
                )

            # 3. 도구 실행 결과를 Gemini에게 전달하여 집사 페르소나 응답 생성
            try:
                user_content = types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
                model_call_content = response.candidates[0].content
                tool_content = types.Content(
                    role="tool",
                    parts=tool_response_parts,
                )

                followup_resp = await gemini_client.aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=[user_content, model_call_content, tool_content],
                    config=types.GenerateContentConfig(
                        tools=GEMINI_TOOLS,
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7,
                    ),
                )
                final_text = followup_resp.text or "\n".join(tool_results)
            except Exception as followup_err:
                logger.warning(f"도구 결과 후속 응답 생성 실패, 결과 텍스트 직접 전송: {followup_err}")
                final_text = "\n".join(tool_results)

            await send_safely(message, final_text)

        else:
            # 도구 호출이 없는 일반 질의응답
            final_text = response.text or "주인님, 요청하신 내용을 정상적으로 확인하였습니다."
            await send_safely(message, final_text)

    except Exception as e:
        logger.error(f"Gemini API 통신 에러: {e}")
        await send_safely(
            message,
            f"주인님, 죄송합니다. AI 서비스와 통신하는 과정에서 오류가 발생하였습니다.\n"
            f"`오류 세부 내용: {e}`"
        )


# ==============================================================================
# 5. Render 무료 웹 서비스용 aiohttp 백그라운드 웹 서버
# ==============================================================================
async def create_web_app() -> web.Application:
    app = web.Application()

    async def root_handler(request: web.Request) -> web.Response:
        bot_user_name = str(bot.user) if bot.user else "연결 중..."
        guild_count = len(bot.guilds) if bot.is_ready() else 0
        data = {
            "status": "healthy",
            "bot": bot_user_name,
            "guilds": guild_count,
            "message": "AI Discord Butler Web Service is running on Render 24/7.",
        }
        return web.json_response(data, status=200)

    async def health_handler(request: web.Request) -> web.Response:
        return web.Response(text="OK", status=200)

    app.router.add_get("/", root_handler)
    app.router.add_get("/health", health_handler)
    return app


async def main():
    logger.info("🚀 AI 디스코드 관리 봇 시스템을 시작합니다...")

    # 1. aiohttp 경량 웹 서버 백그라운드 가동 (Render 포트 바인딩)
    app = await create_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    logger.info(f"🌐 HTTP 웹 서버가 포트 {PORT} (0.0.0.0:{PORT})에 성공적으로 바인딩되었습니다.")

    # 2. 디스코드 봇 시작 (동일 이벤트 루프에서 실행)
    try:
        await bot.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.critical("❌ 디스코드 토큰이 올바르지 않습니다. DISCORD_TOKEN 값을 확인해 주세요.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"❌ 봇 구동 중 치명적 오류 발생: {e}")
        sys.exit(1)
    finally:
        logger.info("시스템 종료 절차를 진행합니다...")
        await runner.cleanup()
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 프로세스가 중단되었습니다.")
