# 一二 × 布布 × 点仔：Codex 宠物

一套可在 Codex Desktop 中切换使用的三角色宠物包，包含“一二”“布布”和“点仔”。三个角色都有完整工作状态动画，并可在每天 22:00–次日 08:00 自动进入夜间待机：没有任务时睡觉，工作、等待确认或检查时保持原动作。

> 这是非官方的粉丝制作版本。公开发布或再分发角色素材前，请先取得角色权利人的授权；详见 [ASSET-NOTICE.md](ASSET-NOTICE.md)。

## 预览

| 一二 | 布布 | 点仔 |
| --- | --- | --- |
| ![一二待机动画](docs/previews/yier-idle.gif) | ![布布待机动画](docs/previews/bubu-idle.gif) | ![点仔待机动画](docs/previews/dianzai-idle.gif) |

- [一二完整动作表](docs/yier-contact-sheet.png)
- [布布完整动作表](docs/bubu-contact-sheet.png)
- [点仔完整动作表（v2，含 16 个视线方向）](docs/dianzai-contact-sheet.png)

| 一二夜间待机 | 布布夜间待机 | 点仔夜间待机 |
| --- | --- | --- |
| ![一二睡眠动画](docs/previews/yier-sleep.gif) | ![布布睡眠动画](docs/previews/bubu-sleep.gif) | ![点仔睡眠动画](docs/previews/dianzai-sleep.gif) |

- [一二夜间动作表：仅待机行睡觉](docs/yier-sleep-contact-sheet.png)
- [布布夜间动作表：仅待机行睡觉](docs/bubu-sleep-contact-sheet.png)
- [点仔夜间动作表：仅待机行睡觉](docs/dianzai-sleep-contact-sheet.png)

## 一键安装（macOS）

下载并解压项目后，在项目目录运行：

```bash
bash install.sh
```

脚本会：

1. 校验宠物文件是否完整；
2. 备份本机已有的同名宠物；
3. 安装到 `~/.codex/pets/yier`、`~/.codex/pets/bubu` 和 `~/.codex/pets/dianzai`。

安装后重启 Codex，进入：

```text
设置 → 外观 → Pets
```

选择“一二”“布布”或“点仔”即可切换。

## 自动睡眠模式（macOS）

安装普通宠物后，在项目目录运行：

```bash
bash install-sleep-mode.sh
```

睡眠模式会：

1. 保持设置中只有“一二”“布布”和“点仔”三个原角色，不注册独立睡觉版；
2. 每天 22:00 将三个角色的待机行动作换成睡觉；
3. 工作、等待确认、检查等其他状态继续使用原动作；
4. 每天 08:00 恢复普通待机；
5. 每 5 分钟校正一次，并在登录或电脑唤醒后按当前时间立即校正。

运行中的 Codex 会直接刷新宠物浮窗，不需要整晚重启应用。本机若没有开启 Codex 调试端口，图集仍会切换，并在下次启动 Codex 时生效。

手动测试：

```bash
python3 ~/.codex/pet-sleep-mode/pet_sleep_scheduler.py --mode sleep
python3 ~/.codex/pet-sleep-mode/pet_sleep_scheduler.py --mode awake
```

可恢复地停用：

```bash
bash uninstall-sleep-mode.sh
```

## Git 安装

直接克隆公开仓库：

```bash
git clone https://github.com/skye-luo/yier-bubu-codex-pets.git
cd yier-bubu-codex-pets
bash install.sh
bash install-sleep-mode.sh
```

## 手动安装

将以下三个目录完整复制到 `~/.codex/pets/`：

```text
pets/yier
pets/bubu
pets/dianzai
```

不要只复制图片；每个目录中的 `pet.json` 和 `spritesheet.webp` 必须放在一起。

## 校验与卸载

校验下载内容：

```bash
bash verify.sh
```

可恢复地卸载：

```bash
bash uninstall.sh
```

卸载脚本不会直接删除文件，而是将宠物移动到 `~/.codex/pets-backups/`。

## 项目结构

```text
.
├── pets/
│   ├── yier/
│   │   ├── pet.json
│   │   ├── spritesheet.webp
│   │   └── spritesheet-night.webp
│   ├── bubu/
│   │   ├── pet.json
│   │   ├── spritesheet.webp
│   │   └── spritesheet-night.webp
│   └── dianzai/
│       ├── pet.json
│       ├── spritesheet.webp
│       └── spritesheet-night.webp
├── sleep-source/
│   ├── yier.webp
│   ├── bubu.webp
│   └── dianzai.png
├── docs/
├── launchd/
├── scripts/
├── install.sh
├── install-sleep-mode.sh
├── uninstall.sh
├── uninstall-sleep-mode.sh
├── verify.sh
└── SHA256SUMS
```

## 许可说明

安装脚本和项目说明采用 MIT 许可，见 [LICENSE-CODE.md](LICENSE-CODE.md)。角色名称、形象、动画图集及预览图片不在 MIT 许可范围内，详见 [ASSET-NOTICE.md](ASSET-NOTICE.md)。
