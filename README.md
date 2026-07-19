# 一二 × 布布：Codex 双宠物

一套可在 Codex Desktop 中切换使用的双角色宠物包，包含“一二”和“布布”。每个角色都有 9 种工作状态动画。

> 这是非官方的粉丝制作版本。公开发布或再分发角色素材前，请先取得角色权利人的授权；详见 [ASSET-NOTICE.md](ASSET-NOTICE.md)。

## 预览

| 一二 | 布布 |
| --- | --- |
| ![一二待机动画](docs/previews/yier-idle.gif) | ![布布待机动画](docs/previews/bubu-idle.gif) |

- [一二完整动作表](docs/yier-contact-sheet.png)
- [布布完整动作表](docs/bubu-contact-sheet.png)

## 一键安装（macOS）

下载并解压项目后，在项目目录运行：

```bash
bash install.sh
```

脚本会：

1. 校验宠物文件是否完整；
2. 备份本机已有的同名宠物；
3. 安装到 `~/.codex/pets/yier` 和 `~/.codex/pets/bubu`。

安装后重启 Codex，进入：

```text
设置 → 外观 → Pets
```

选择“一二”或“布布”即可切换。

## Git 安装

仓库公开后可以使用：

```bash
git clone <GitHub 仓库地址>
cd yier-bubu-codex-pets
bash install.sh
```

## 手动安装

将以下两个目录完整复制到 `~/.codex/pets/`：

```text
pets/yier
pets/bubu
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
│   │   └── spritesheet.webp
│   └── bubu/
│       ├── pet.json
│       └── spritesheet.webp
├── docs/
├── install.sh
├── uninstall.sh
├── verify.sh
└── SHA256SUMS
```

## 许可说明

安装脚本和项目说明采用 MIT 许可，见 [LICENSE-CODE.md](LICENSE-CODE.md)。角色名称、形象、动画图集及预览图片不在 MIT 许可范围内，详见 [ASSET-NOTICE.md](ASSET-NOTICE.md)。
