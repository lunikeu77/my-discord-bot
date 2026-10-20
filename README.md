# 🤖 개인 서버 전담 관리 AI 디스코드 봇 (AI Discord Butler)

Google 최신 **Gemini 2.5 Flash**의 강력한 자연어 추론 및 **함수 호출(Function Calling / Tools)** 기술을 활용한 디스코드 개인 서버 관리용 AI 집사 봇입니다.

사용자의 일상 대화나 자연어 요청("공지방 텍스트 채널 파줘", "채팅 30개 청소해", "음악봇 데려와")을 정확히 이해하고 디스코드 관리자 작업을 자동으로 수행하며, **Render.com 무료 웹 서비스(Web Service)** 환경에 배포하여 내 PC가 꺼져 있어도 24시간 365일 무중단으로 구동됩니다.

---

## 📋 핵심 기능 및 도구(Tools) 목록

| 기능 (도구) | 설명 | 자연어 호출 예시 |
| :--- | :--- | :--- |
| **채널 생성** (`create_channel`) | 텍스트 또는 음성 채널을 지정한 이름으로 생성합니다. | `!공지사항 텍스트 채널 만들어줘`<br>`!음악감상 음성 채널 파줘` |
| **채널 삭제** (`delete_channel`) | 특정 채널 이름이나 현재 접속 중인 채널을 삭제합니다. | `!이 채널 삭제해`<br>`!임시방 채널 삭제해줘` |
| **역할 생성** (`create_role`) | 서버에 새로운 역할을 자동으로 생성합니다. | `!VIP 역할 만들어줘`<br>`!게스트 역할 추가해줘` |
| **메시지 청소** (`purge_messages`) | 현재 채널의 최근 메시지를 최대 100개까지 일괄 삭제합니다. | `!채팅 30개 청소해줘`<br>`!메시지 15개 지워줘` |
| **봇 초대 링크** (`invite_bot_link`) | 디스코드 보안 정책을 안내하고 Top.gg 공식 검색 링크를 제공합니다. | `!음악봇 데려와`<br>`!하이드라 봇 초대 링크 줘` |
| **AI 집사 대화** | 도구 실행 결과 보고 및 친절하고 유능한 집사 페르소나 일반 상담 | `!안녕 넌 누구니?`<br>`!서버 운영 꿀팁 알려줘` |

---

## 🛠️ 사전 준비 (필수 키 발급)

1. **디스코드 봇 토큰 발급**:
   - [Discord Developer Portal](https://discord.com/developers/applications) 접속 → `New Application` 생성
   - 좌측 **Bot** 탭 이동 → `Reset Token` 클릭하여 토큰 복사 (**DISCORD_TOKEN**)
   - **중요**: 같은 Bot 탭 아래의 **Privileged Gateway Intents** 3가지 항목을 모두 켭니다 (`ON`):
     - ✅ **Presence Intent**
     - ✅ **Server Members Intent**
     - ✅ **Message Content Intent** (필수!)
   - 좌측 **OAuth2** → **URL Generator** 이동:
     - Scopes: `bot` 체크
     - Bot Permissions: `Administrator` (또는 채널 관리, 역할 관리, 메시지 관리 등) 체크
     - 하단 생성된 URL을 브라우저에 붙여넣어 내 디스코드 서버에 봇을 초대합니다.

2. **구글 Gemini API 키 발급**:
   - [Google AI Studio](https://aistudio.google.com/app/apikey) 접속 → Google 계정 로그인
   - `Create API key` 클릭 후 생성된 키 복사 (**GEMINI_API_KEY**)

---

## 🚀 코딩 몰라도 가능한 3단계 배포 가이드

### [1단계] GitHub 저장소에 프로젝트 파일 올리기

#### 방법 A. 웹 브라우저로 올리기 (초보자 추천)
1. [GitHub](https://github.com)에 로그인 후 우측 상단 `+` 버튼 → **New repository** 클릭.
2. 저장소 이름(예: `discord-ai-butler`) 입력 후 **Public** 또는 **Private** 선택 → `Create repository` 클릭.
3. 생성된 빈 저장소 화면에서 **"uploading an existing file"** 파란색 링크 클릭.
4. 이 폴더에 있는 파일들(`bot.py`, `requirements.txt`, `.env.example`, `README.md`)을 드래그 앤 드롭으로 업로드합니다.
5. 하단의 **Commit changes** 녹색 버튼을 누르면 업로드 완료!

#### 방법 B. Git CLI로 올리기 (개발자용)
```bash
git init
git add .
git commit -m "feat: 디스코드 AI 관리자 봇 초기 구성"
git branch -M main
git remote add origin https://github.com/당신의깃허브계정/discord-ai-butler.git
git push -u origin main
```

> [!WARNING]
> 본인의 실제 토큰이나 API 키가 적힌 `.env` 파일은 절대 GitHub 저장소에 올리지 마세요!

---

### [2단계] Render.com에 무료 웹 서비스(Web Service) 연동 및 배포

Render의 **Web Service(무료)**는 웹 포트가 열려 있어야 정상 구동되므로, 이 프로젝트는 `aiohttp` 경량 웹 서버가 내장되어 있습니다.

1. [Render.com](https://render.com)에 가입 후 로그인 (GitHub 계정 연동 추천).
2. 대시보드 우측 상단 **`New +`** 버튼 클릭 → **`Web Service`** 선택.
3. **Build and deploy from a Git repository** 선택 후 `Next`.
4. 1단계에서 생성한 GitHub 저장소(`discord-ai-butler`)를 찾아 **Connect** 클릭.
5. 배포 설정을 아래 표와 똑같이 입력합니다:

| 항목 (Field) | 설정할 값 (Value) | 설명 |
| :--- | :--- | :--- |
| **Name** | `my-discord-ai-bot` | 원하는 서비스 이름 입력 |
| **Region** | `Singapore` | 한국과 지연시간이 가장 가까운 리전 추천 |
| **Branch** | `main` | 기본 브랜치 |
| **Runtime** | `Python 3` | 파이썬 런타임 선택 |
| **Build Command** | `pip install -r requirements.txt` | 패키지 설치 명령어 |
| **Start Command** | `python bot.py` | 봇 실행 명령어 |
| **Instance Type** | `Free` (0$/month) | 무료 티어 선택 |

6. 아래로 스크롤하여 **Environment Variables (환경 변수)** 섹션에서 `Add Environment Variable`을 눌러 등록합니다:

| Key (키) | Value (값) |
| :--- | :--- |
| `DISCORD_TOKEN` | *사전 준비에서 복사한 디스코드 봇 토큰* |
| `GEMINI_API_KEY` | *Google AI Studio에서 발급받은 Gemini API 키* |
| `PORT` | `8080` *(또는 비워두어도 Render가 자동 할당)* |

7. 맨 아래 **`Deploy Web Service`** 버튼을 클릭합니다.
8. 로그 창에 `HTTP 웹 서버가 포트 8080에 바인딩되었습니다.` 및 `AI 관리자 디스코드 봇 로그인 완료`가 뜨면 배포 완료입니다!

---

### 💡 [보너스 꿀팁] Render 무료 플랜 24시간 무중단 유지하기

Render 무료 웹 서비스는 15분 동안 웹 접속(HTTP 요청)이 없으면 슬립(Sleep) 상태로 전환됩니다.  
봇을 365일 깨어있게 유지하려면 무료 핑 서비스에 내 웹 서비스 주소를 등록하세요:

1. Render 대시보드 상단에 부여된 웹 서비스 주소(예: `https://my-discord-ai-bot.onrender.com`)를 복사합니다.
2. [UptimeRobot](https://uptimerobot.com) (무료)에 가입합니다.
3. **Add New Monitor** 클릭:
   - Monitor Type: `HTTP(s)`
   - Friendly Name: `Discord Bot Ping`
   - URL (or IP): 복사한 Render URL 붙여넣기 (`https://my-discord-ai-bot.onrender.com/health`)
   - Monitoring Interval: `Every 5 minutes` (5분 간격)
4. 저장하면 끝! 5분마다 Render에 신호를 보내 봇이 절대 꺼지지 않고 24시간 실행됩니다.

---

### [3단계] 디스코드에서 봇 호출 및 테스트하기

봇을 부르는 방법은 **3가지**입니다:
- **느낌표 접두사**: `!명령어`
- **봇 멘션**: `@봇이름 명령어`
- **1:1 개인 DM**: 봇을 클릭해 개인 메시지로 대화

#### 🗣️ 테스트 예시 문장 목록

##### 1. 채널 생성
- `!공지사항 텍스트 채널 하나 파줘`
- `!자유토론방 텍스트 채널 만들어줘`
- `!노래방 음성 채널 만들어줘`

##### 2. 채널 삭제
- `!이 채널 삭제해` *(현재 채널 삭제 알림 후 채널 제거)*
- `!임시채널 삭제해줘` *(지정한 이름의 채널 제거)*

##### 3. 역할 생성
- `!VIP 멤버 역할 생성해줘`
- `!서버관리자 역할 만들어줘`

##### 4. 메시지 청소
- `!채팅 20개 청소해줘`
- `!최근 메시지 50개 삭제해`

##### 5. 봇 초대 링크 문의
- `!음악봇 데려와`
- `!미에봇 초대하고 싶어`
- `!노래봇 초대 링크 알려줘`

##### 6. 일반 대화 및 서버 운영 질의응답
- `!안녕! 넌 무엇을 할 수 있는 봇이니?`
- `!디스코드 서버 멤버를 늘리려면 어떻게 해야 할까?`
- `!오늘 날씨 어때?`

---

## 📂 프로젝트 파일 구조

```
디코 개인봇/
├── bot.py             # 메인 실행 파일 (aiohttp 웹서버 + discord.py + Gemini 2.5 Flash Tools)
├── requirements.txt   # Render 설치용 필수 패키지 목록
├── .env.example       # 환경 변수 설정 템플릿
├── .gitignore         # 보안용 Git 제외 목록
└── README.md          # 초보자용 배포 및 사용 가이드
```

---

## ❓ 자주 묻는 질문 (FAQ)

**Q. 봇이 온라인인데 멘션이나 `!`를 쳐도 대답이 없어요.**  
A. Discord Developer Portal에서 **Bot** 탭의 `Message Content Intent`가 켜져 있는지 확인하세요. 이 옵션이 꺼져 있으면 봇이 사용자의 메시지 내용을 읽지 못합니다.

**Q. 권한 부족 에러가 발생해요.**  
A. 디스코드 서버 설정 > `역할(Roles)`에서 **봇의 역할 순위가 생성/삭제할 역할이나 채널보다 더 상위에 위치**해야 합니다. 봇 역할을 드래그해서 상위로 올려주세요.

**Q. 로컬 PC에서 테스트하고 싶어요.**  
A. `.env.example` 파일을 복사하여 `.env`로 이름을 바꾼 뒤 실제 토큰과 API 키를 적고 `pip install -r requirements.txt` 후 `python bot.py`를 실행하시면 됩니다.
