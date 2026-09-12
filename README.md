# 一二 × 布布 × 点仔：Codex 宠物

统一的 Codex Desktop 宠物项目，包含“一二”“布布”和“点仔”。v2.0.0 更新了一二、布布的形象和循环动作：白天精神满满，查资料抱书、写代码抱电脑、写作抱本子；晚上 22:00–次日 08:00 空闲时自动睡觉。点仔原有形象、完整工作动画和夜间睡眠保持不变。

原 `yier-bubu-codex-pet`（单数）项目的 Windows 安装和任务识别功能已合并至本项目（复数 `pets`）。今后的更新以这里为准；旧仓库、历史版本和下载链接保留。

> 非官方、非商业的粉丝体验版本。角色素材不在 MIT 许可范围内，详见 [ASSET-NOTICE.md](ASSET-NOTICE.md)。

## 预览

![实际安装素材的八种状态](social/xiaohongshu/02-day-night.png)

| 状态 | 常驻造型 |
| --- | --- |
| 白天待机 | 挺起小身体，呼吸、眨眼 |
| 查找资料 | 抱书和放大镜 |
| 写代码 / 通用工作 | 抱电脑，持续敲键盘 |
| 写作规划 | 抱本子，拿铅笔 |
| 检查结果 | 抱检查板，认真核对 |
| 等你回应 | 坐好，期待地望向你 |
| 遇到问题 | 挠挠头，有点困惑 |
| 夜间空闲 | 枕着小枕头睡觉 |

造型会在对应任务阶段循环保持；拖动、点击和鼠标注视仍使用原生交互。每个角色始终只有一个宠物 ID。

| 一二 | 布布 |
| --- | --- |
| ![一二待机动画](docs/previews/yier-idle.gif) | ![布布待机动画](docs/previews/bubu-idle.gif) |

点仔继续保留：[白天动画](docs/previews/dianzai-idle.gif) · [夜间动画](docs/previews/dianzai-sleep.gif) · [完整动作表](docs/dianzai-contact-sheet.png)。本次新增的三种任务工作造型仅适用于一二、布布。

| 一二夜间待机 | 布布夜间待机 |
| --- | --- |
| ![一二睡眠动画](docs/previews/yier-sleep.gif) | ![布布睡眠动画](docs/previews/bubu-sleep.gif) |

- [一二完整动作表](docs/yier-contact-sheet.png)
- [布布完整动作表](docs/bubu-contact-sheet.png)
- [一二夜间动作表：仅待机行睡觉](docs/yier-sleep-contact-sheet.png)
- [布布夜间动作表：仅待机行睡觉](docs/bubu-sleep-contact-sheet.png)
- [最初确认的形象设计稿](docs/state-concept.png)

## 一行安装

需要支持 v2 自定义宠物图集的 Codex Desktop。若旧版应用不显示宠物或注视动作异常，请先更新应用。下面命令同时适用于首次安装和从旧项目升级。

### Windows

打开 PowerShell，复制这一行（不需要提前安装 Git）：

```powershell
irm https://raw.githubusercontent.com/skye-luo/yier-bubu-codex-pets/v2.0.0/quick-install.ps1 | iex
```

这条命令会：

- 将“一二”“布布”和“点仔”安装到 `%USERPROFILE%\.codex\pets`；
- 注册一个当前用户的 Windows 定时任务，每分钟运行一次，运行期间每 5 秒检查任务类型与本地时间；
- 每天 22:00–次日 08:00 只把待机动作换成睡觉，其他工作状态不变；
- 不创建“一二（睡觉）”或“布布（睡觉）”等独立角色。

安装完成后重启 ChatGPT/Codex，进入 `设置 → Pets`，选择“一二”或“布布”。如果睡眠时间切换后浮窗没有立即刷新，下次启动应用时一定会读取新的图集。

如果希望先查看脚本再执行：

```powershell
git clone --branch v2.0.0 https://github.com/skye-luo/yier-bubu-codex-pets.git
cd yier-bubu-codex-pets
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\install-sleep-mode.ps1
```

手动测试 Windows 睡眠切换：

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.codex\pet-sleep-mode\pet_sleep_scheduler.ps1" -Mode Sleep
powershell -ExecutionPolicy Bypass -File "$HOME\.codex\pet-sleep-mode\pet_sleep_scheduler.ps1" -Mode Awake
```

Windows 卸载（文件会移动到备份目录，不会直接删除）：

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall-sleep-mode.ps1
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

### macOS

```bash
curl -fsSL https://raw.githubusercontent.com/skye-luo/yier-bubu-codex-pets/v2.0.0/quick-install.sh | bash
```

这条命令会安装两个宠物并启用 22:00–08:00 自动睡眠。安装完成后重启 Codex，进入 `设置 → 外观 → Pets`，选择“一二”或“布布”。

如果你希望先查看脚本再执行，也可以使用透明的分步安装：

```bash
git clone --branch v2.0.0 https://github.com/skye-luo/yier-bubu-codex-pets.git
cd yier-bubu-codex-pets
bash install.sh
bash install-sleep-mode.sh
```

`install-sleep-mode.sh` 会启用自动睡眠：

- 设置中始终只有“一二”和“布布”，不会注册独立睡觉角色；
- 每天 22:00 将待机行换成睡觉，08:00 恢复普通待机；
- 工作、等待确认、检查等其他状态不变；
- 每 10 秒检查任务类型和本地时间，并在登录或唤醒后校正；
- Codex 已运行时会尝试立即刷新宠物浮窗，否则下次启动时生效。

手动测试：

```bash
python3 ~/.codex/pet-sleep-mode/pet_sleep_scheduler.py --mode sleep
python3 ~/.codex/pet-sleep-mode/pet_sleep_scheduler.py --mode awake
```

## 自动识别的范围

运行、等待回应、检查结果和错误由应用的原生宠物状态决定。附加调度器在本机检查近期本地任务日志，根据当前请求与工具调用中的关键词，选择查资料、写代码或写作造型；同一任务内至少保持 30 秒，避免来回闪动。未识别的任务使用抱电脑的通用工作造型。云端任务或没有本地日志的任务不能保证细分识别。

只读取最近三天目录中、最近 30 分钟更新的至多 16 份日志末尾，每份最多 512 KiB。请求和工具文本不上传、不写入状态文件；状态文件只保存类别、匿名任务标记和切换时间。旧版本应用、未开放本地实时刷新接口的环境可能需要重启应用才能读取切换后的图集；调度器不会自动开启调试端口。

已安装旧版的用户重新运行对应系统的一行安装命令即可更新，旧宠物和定时组件会备份到 `~/.codex/pets-backups/`。

## 校验与卸载

```bash
bash verify.sh
bash uninstall-sleep-mode.sh
bash uninstall.sh
```

卸载脚本不会直接删除文件，而会移动到 `~/.codex/pets-backups/`，方便恢复。

## 重新组装动作变体

`state-source/` 保存本版已经清理透明边缘的六帧素材行；`sleep-source/` 保留旧版来源，仅供历史参考。安装不需要 Pillow；只有重新组装图片时需要。

```bash
python3 scripts/build_night_atlas.py --awake pets/yier/spritesheet.webp --sleep-row state-source/yier/sleep.webp --output pets/yier/spritesheet-night.webp
python3 scripts/build_activity_atlases.py --pet-dir pets/yier --research-row state-source/yier/research.webp --writing-row state-source/yier/writing.webp
```

布布将命令中的 `yier` 换成 `bubu`。脚本只拼装已确认素材，不生成或重画姿势。修改后运行 `node scripts/update_checksums.mjs` 和 `bash verify.sh`。

## 项目结构

```text
.
├── pets/
│   ├── yier/
│   ├── bubu/
│   └── dianzai/
├── sleep-source/
├── state-source/
├── docs/
├── scripts/
├── launchd/
├── social/xiaohongshu/
├── install.ps1
├── install-sleep-mode.ps1
├── quick-install.ps1
├── uninstall.ps1
├── uninstall-sleep-mode.ps1
├── verify.ps1
├── install.sh
├── install-sleep-mode.sh
├── quick-install.sh
├── uninstall.sh
├── uninstall-sleep-mode.sh
└── verify.sh
```

安装脚本和项目说明采用 MIT 许可，见 [LICENSE-CODE.md](LICENSE-CODE.md)。角色名称、形象、动画图集及预览图片不在 MIT 许可范围内。
