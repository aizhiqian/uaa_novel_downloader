#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import os
from pathlib import Path
from src.auth import AuthManager
from src.downloader import NovelDownloader
from src.utils import ChapterModifier, ExtractScriptGenerator
from src.progress import ProgressManager
from src.logger import setup_logger
from src.config import Config, setup_directories

def setup_command(args):
    """初始化项目目录结构和配置"""
    try:
        setup_directories()
        print("✅ 项目初始化完成！请编辑config目录下的users.txt文件添加您的账号信息")
    except KeyboardInterrupt:
        print("\n👋 操作已取消")
        sys.exit(0)

def login_command(args):
    """登录并获取Cookie"""
    try:
        auth = AuthManager()
        if args.user:
            auth.login(user_id=args.user)
        else:
            auth.login()
    except KeyboardInterrupt:
        print("\n👋 登录已取消")
        sys.exit(0)

def download_command(args):
    """下载小说"""
    logger = setup_logger('downloader')
    try:
        downloader = NovelDownloader(user_id=args.user)

        # 交互式使用
        if not args.novel_id:
            downloader.interactive_download()
            return

        # 验证传入参数的合法性
        if args.count and args.end:
            logger.error("不能同时指定 --count 和 --end 参数")
            print("❌ 错误: 不能同时指定 --count 和 --end 参数")
            return

        # 计算结束章节
        end_chapter = None
        if args.end:
            end_chapter = args.end
        elif args.count:
            end_chapter = args.start + args.count - 1

        # 下载
        downloader.download_novel(
            novel_id=args.novel_id,
            start_chapter=args.start,
            end_chapter=end_chapter
        )
    except KeyboardInterrupt:
        print("\n👋 下载已取消")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"下载过程中发生错误: {str(e)}")
        print(f"❌ 下载失败: {str(e)}")

def progress_command(args):
    """管理下载进度"""
    try:
        progress_mgr = ProgressManager()

        # 交互式使用
        if not any([args.view, args.resume, args.clear]):
            progress_mgr.interactive_manage()
            return

        if args.view:
            progress_mgr.view_progress()
        elif args.resume:
            if not args.novel_id:
                print("❌ 使用 --resume 时必须指定 --novel-id 参数")
                return

            # 获取进度并继续下载
            progress = progress_mgr.get_novel_progress(args.novel_id)
            if progress:
                print(f"📚 继续下载《{progress['title']}》，从第{progress['next_chapter']}章开始")
                downloader = NovelDownloader()
                downloader.download_novel(
                    novel_id=args.novel_id,
                    start_chapter=progress['next_chapter']
                )
            else:
                print(f"❌ 未找到小说ID {args.novel_id} 的下载进度")

        elif args.clear:
            if args.novel_id:
                progress_mgr.clear_progress(args.novel_id)
                print(f"✅ 已清除小说ID {args.novel_id} 的下载进度")
            else:
                progress_mgr.clear_all_progress()
                print("✅ 已清除所有下载进度")
    except KeyboardInterrupt:
        print("\n👋 进度管理已取消")
        sys.exit(0)

def modify_command(args):
    """修改章节编号"""
    try:
        modifier = ChapterModifier()

        if args.file:
            if args.start_name and args.end_name and args.increment is not None:
                # 使用章节名修改
                modifier.modify_chapters_by_name(args.file, args.start_name, args.end_name, args.increment)
            elif args.start and args.end is not None and args.increment is not None:
                # 使用章节编号修改
                modifier.modify_chapters(args.file, args.start, args.end, args.increment)
            else:
                print("❌ 请指定修改参数")
        else:
            # 交互式使用
            modifier.interactive_modify()
    except KeyboardInterrupt:
        print("\n👋 章节修改已取消")
        sys.exit(0)

def extract_command(args):
    """生成章节提取脚本"""
    try:
        generator = ExtractScriptGenerator()
        generator.generate_script()
    except KeyboardInterrupt:
        print("\n👋 脚本生成已取消")
        sys.exit(0)

def main():
    """主函数，解析命令行参数并执行对应命令"""
    parser = argparse.ArgumentParser(description='UAA小说下载器')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # setup命令
    setup_parser = subparsers.add_parser('setup', help='初始化项目目录结构')

    # login命令
    login_parser = subparsers.add_parser('login', help='登录并获取Cookie')
    login_parser.add_argument('--user', help='指定用户ID或"all"表示所有用户')

    # download命令
    download_parser = subparsers.add_parser('download', help='下载小说')
    download_parser.add_argument('novel_id', nargs='?', help='小说ID')
    download_parser.add_argument('--start', type=int, default=1, help='起始章节 (默认: 1)')
    download_parser.add_argument('--end', type=int, help='结束章节')
    download_parser.add_argument('--count', type=int, help='要下载的章节数量')
    download_parser.add_argument('--user', type=int, help='指定用户ID')

    # progress命令
    progress_parser = subparsers.add_parser('progress', help='管理下载进度')
    progress_parser.add_argument('--view', action='store_true', help='查看所有进度')
    progress_parser.add_argument('--resume', action='store_true', help='继续下载')
    progress_parser.add_argument('--clear', action='store_true', help='清除进度')
    progress_parser.add_argument('--novel-id', help='小说ID')

    # modify命令
    modify_parser = subparsers.add_parser('modify', help='修改章节编号')
    modify_parser.add_argument('--file', help='文件路径')
    modify_parser.add_argument('--start', type=int, help='开始章节编号')
    modify_parser.add_argument('--end', type=int, help='结束章节编号')
    modify_parser.add_argument('--start-name', help='开始章节名称')
    modify_parser.add_argument('--end-name', help='结束章节名称')
    modify_parser.add_argument('--increment', type=int, default=1, help='增量值 (默认: 1)')

    # extract命令
    extract_parser = subparsers.add_parser('extract', help='生成浏览器章节提取脚本')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行对应的命令
    commands = {
        'setup': setup_command,
        'login': login_command,
        'download': download_command,
        'progress': progress_command,
        'modify': modify_command,
        'extract': extract_command
    }

    commands[args.command](args)

if __name__ == "__main__":
    main()
