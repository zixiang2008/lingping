# Lingping.Skills

面向 Lingping Club 学员的课程、预定、Google 日历和上课提醒 Agent Skill。

它会读取 Lingping 网站上的课程与个人预定，将结果转换为本地时区，并按照明确规则同步至 Google 日历。通知支持 Hermes 通讯渠道、Google 日历和 macOS 系统通知，并通过单一主通道避免重复提醒。

## 功能

- 每晚生成第二天课程与当前预定汇总。
- 同步所有已报名课程到 Google 日历。
- 已报名课程默认提前 60 分钟提醒，并标记为忙碌。
- 将清迈线下英文课和线下英文语言交换活动作为“未报名”参考事件同步到日历。
- 未报名事件无提醒、标记为空闲，不影响日历可用时间。
- 日历备注包含课程内容、老师、报名状态、余位、来源及稳定的 Session ID。
- 使用 Session ID 增量更新，避免重复创建事件。
- 自动选择 Hermes、Google 日历或本机通知作为提醒渠道。
- 所有用户提醒和状态文本使用中文。
- 不会自动报课、取消课程或删除历史日历事件。

## 工作方式

```text
Lingping 网站
   ├─ 公开课程目录
   └─ 当前用户未来预定
          ↓
   lingping.py 标准化
          ↓
   ├─ 次日中文汇总
   ├─ Google 日历增量同步
   └─ 提前一小时通知路由
          ├─ Hermes（可用且已绑定时优先）
          ├─ Google 日历
          └─ macOS 系统通知
```

## 日历同步规则

| 类型 | 是否同步 | 标题前缀 | 提醒 | 日历占用 |
| --- | --- | --- | --- | --- |
| 已报名课程 | 是，所有语言 | `【已报名】` | 提前 60 分钟 | 忙碌 |
| 未报名的清迈线下英文课 | 是 | `【未报名】` | 无 | 空闲 |
| 未报名的线下英文语言交换 | 是 | `【未报名】` | 无 | 空闲 |
| 其他未报名课程 | 否 | — | — | — |

同步程序不会自动删除已经存在的 Lingping 日历事件。网站课程取消、消失或大幅变更时，应先列出差异，由用户确认后再删除。

## 安装

### Codex

将技能目录复制到个人技能目录：

```bash
mkdir -p ~/.codex/skills
cp -R .agents/skills/lingping-class-assistant ~/.codex/skills/
```

也可以保留仓库中的 `.agents/skills/` 结构，作为项目级可移植 Skill 使用。

### 其他支持 Agent Skills 的工具

- Claude Code：复制到 `~/.claude/skills/` 或项目的 `.claude/skills/`。
- Cursor：优先保留 `.agents/skills/`，也可复制到项目的 `.cursor/skills/`。
- OpenCode：保留 `.agents/skills/`，或复制到 `~/.config/opencode/skills/`。

不同工具对定时任务、Google Calendar 连接器和 Hermes 的支持程度不同。Skill 的核心课程读取脚本可以独立运行；日历写入和定时自动化需要宿主工具具备相应能力。

## 初次配置

创建个人配置文件：

```bash
mkdir -p ~/.config/lingping
cp .agents/skills/lingping-class-assistant/references/config.example.json \
  ~/.config/lingping/config.json
```

编辑 `~/.config/lingping/config.json`：

```json
{
  "lingping_username": "your-lingping-email@example.com",
  "timezone": "Asia/Bangkok",
  "calendar_id": "primary",
  "notification": {
    "mode": "auto",
    "hermes_channel": "",
    "fallbacks": ["google_calendar", "macos_notification"],
    "avoid_duplicates": true
  }
}
```

字段说明：

- `lingping_username`：Lingping 登录用户名。不要把个人账号直接写入公开仓库。
- `timezone`：IANA 时区，例如 `Asia/Bangkok`。
- `calendar_id`：Google 主日历使用 `primary`；也可填写已授权的其他日历 ID。
- `notification.mode`：推荐使用 `auto`，也支持 `hermes`、`google_calendar` 或 `macos_notification`。
- `hermes_channel`：Hermes 已验证的目标通讯渠道；未绑定时保持为空。
- `avoid_duplicates`：为 `true` 时，每次提醒只使用一个主渠道。

## Google 日历授权

Google Calendar 必须通过宿主 Agent 的官方 OAuth/连接器授权。不要把 Google 密码、Cookie、访问令牌或 OAuth 密钥写入配置文件或发送给 Agent。

授权后应先检查当前 Google 账户和目标日历，再执行批量同步。Google 日历事件使用描述中的 `Lingping Session ID` 作为去重键。

## 常用命令

```bash
SCRIPT="${CODEX_HOME:-$HOME/.codex}/skills/lingping-class-assistant/scripts/lingping.py"
```

检查网站连接和数据读取：

```bash
python3 "$SCRIPT" self-test
```

生成第二天课程与预定汇总：

```bash
python3 "$SCRIPT" daily
```

查看未来预定：

```bash
python3 "$SCRIPT" bookings
```

生成日历同步数据：

```bash
python3 "$SCRIPT" calendar-json
```

检查当前通知路线：

```bash
python3 "$SCRIPT" notification-status
```

检查是否存在一小时内开始的已预定课程：

```bash
python3 "$SCRIPT" reminders
```

`reminders` 只在课程距离开始 55–65 分钟时输出，并在本地记录已提醒的 Session ID，防止重复通知。

## 通知选择

`auto` 模式按以下顺序选择：

1. Hermes：仅在网关健康且目标通讯渠道已配置时启用。
2. Google 日历：已报名事件提前 60 分钟弹窗提醒。
3. macOS 通知：仅在日历不可用或用户明确选择时使用。
4. 宿主 Agent 的线程通知：前三种方式均不可用时的最后选择。

仅检测到 `hermes` 命令并不表示 Hermes 可用。必须同时满足：网关健康检查通过、目标渠道已配置、真实测试消息发送成功。启用 Hermes 后，如果 `avoid_duplicates=true`，应避免再发送相同的日历弹窗；Hermes 失败时应先恢复 Google 日历提醒。

## 推荐自动化

在配置文件指定的时区中建立两项任务：

- 每天 21:00：生成次日汇总，更新 Google 日历，检查通知路由。
- 每 5 分钟：仅当主通知渠道是 Hermes 或本机通知时检查临近课程；Google 日历为主渠道时静默退出。

自动化必须是只读课程操作：不得自动报课或取消。日历同步可以创建或更新事件，但删除必须由用户明确确认。

## 安全设计

- 不保存 Google 密码、Cookie、访问令牌或 API 密钥。
- Lingping 网站客户端所需的公开配置在运行时从网站读取，不固化到仓库。
- 个人账号只保存在用户自己的 `~/.config/lingping/config.json`。
- 不输出 Lingping 内部用户 ID、API key 或访问 token。
- Hermes 目标渠道必须由用户配置并通过测试确认。
- 公开发布前可运行以下扫描：

```bash
rg -n -i 'password|token|api[_-]?key|cookie|@gmail\.com|/Users/|userId' .
```

扫描结果中的说明文字和代码变量需要人工判断；真实凭证、个人邮箱与绝对个人路径必须为零。

## 文件结构

```text
.agents/skills/lingping-class-assistant/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── config.example.json
│   ├── notification-routing.md
│   └── site-map.md
└── scripts/
    └── lingping.py
```

## 已知限制

- Lingping 网站或 API 结构变化后，课程目录 ID 和字段映射可能需要更新。
- 当前脚本读取网站未来约九天的课程窗口，与网站公开页面范围保持一致。
- Google Calendar 和定时任务需要宿主 Agent 提供对应连接器或自动化能力。
- macOS 本机通知在电脑休眠或离线时不可靠，因此不建议作为唯一提醒方式。
- Hermes 不同版本的发送参数可能不同；发送前必须读取当前安装版本的帮助信息。

## 故障排查

### 提示“请先配置 lingping_username”

确认 `~/.config/lingping/config.json` 存在，且 `lingping_username` 不是空字符串。

### 网站同步失败

先执行 `self-test`。若网站返回 404，脚本会按“暂无课程/预定”处理；其他网络错误会返回简短错误信息。网站前端结构改变时，检查 `config.js`、`js/auth.js`、首页课程筛选和 `js/booking.js`。

### 日历出现重复事件

搜索事件备注中的 `Lingping Session ID`。同步实现必须先搜索目标时间窗口并更新已有 ID，不能只按标题匹配或无条件创建。

### Hermes 无法使用

运行 `notification-status`，确认网关健康和 `hermes_channel` 已配置。不同 Hermes 版本的命令参数可能不同，请以本机 `hermes send --help` 为准。

## 许可

本项目采用 MIT License。Lingping Club、Google Calendar、Hermes 及相关名称归各自权利人所有。本项目是独立的自动化 Skill，不代表这些服务的官方产品。
