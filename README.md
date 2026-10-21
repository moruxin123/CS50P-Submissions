# CS50P 作业与提交中心

这是用于 [CS50's Introduction to Programming with Python](https://cs50.harvard.edu/python/)
作业、检查和提交记录的仓库。

## 一键使用

双击桌面上的 **CS50P 作业中心**，或者双击仓库根目录的
`START-HERE.cmd`。启动后可以：

1. 选择题目并通过 `check50` 检查
2. 通过官方 `submit50` 提交
3. 运行作业程序
4. 用 VS Code 编写作业代码
5. 在资源管理器中打开题目目录
6. 保存并同步到 GitHub
7. 查看环境状态

不需要手动打开 WSL、激活 Python 虚拟环境或输入课程 slug。Windows
桌面快捷方式会自动完成这些步骤。

## 环境说明

`check50` 和 `submit50` 依赖 Unix 终端功能，因此运行在 Ubuntu WSL 中：

- 发行版：`Ubuntu`
- WSL 用户：`cs50p`
- Python 环境：`/opt/cs50p-venv`
- `check50`：3.5.0
- `submit50`：3.2.1
- 作业账号：`moruxin123`
- 官方提交仓库：`me50/moruxin123`

GitHub 凭据只在启动时临时传给 WSL，不会写入仓库或脚本。
启动器还会在 `%LOCALAPPDATA%\CS50P-Submissions` 保存一份由 Windows
当前用户加密的凭据缓存，避免 `gh` 登录状态偶发读取失败时导致启动器退出。

不要通过双击 `.py` 文件来编写代码。Windows 会把这种操作解释为“运行程序”，
因此终端窗口可能一闪而过。请从作业中心选择 **4. 编写作业代码（VS Code）**。

## 目录结构

每道题有独立目录，文件名与 CS50P 规格一致：

```text
problem_sets/
├── pset0/
│   ├── indoor/
│   │   └── indoor.py
│   └── playback/
│       └── playback.py
├── pset1/
└── ...
```

## 手动运行

平时使用桌面快捷方式即可。需要排查问题时，可以在 Ubuntu 中运行：

```bash
cd /mnt/c/Users/20332/Documents/Codex/2026-10-21/bang
/usr/local/bin/check50 cs50/problems/2022/python/indoor
```

正式交卷前请再次阅读题目和 CS50 的学术诚信要求。仓库中的代码应为你本人
完成的作品。
