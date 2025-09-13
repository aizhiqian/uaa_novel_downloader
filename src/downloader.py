import requests
from bs4 import BeautifulSoup
import time
import re
import sys
from .config import Config
from .auth import AuthManager
from .logger import setup_logger
from .progress import ProgressManager

class NovelDownloader:
    """小说下载器核心类"""

    def __init__(self, user_id=None):
        """初始化下载器"""
        self.logger = setup_logger('downloader')
        self.auth = AuthManager()
        self.progress_mgr = ProgressManager()
        self.session = requests.Session()
        self.user_id = user_id
        self.headers = {
            'User-Agent': Config.USER_AGENT
        }

        # 如果没有指定user_id，提示用户选择
        if user_id is None:
            self.user_id = self._select_user()

        # 获取Cookie，如果失败尝试重新登录
        cookie = self._get_valid_cookie()
        if not cookie:
            print("❌ 无法获取有效Cookie，程序退出")
            sys.exit(1)

        self.headers['Cookie'] = cookie
        self.session.headers.update(self.headers)

        # 确保输出目录存在
        Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _select_user(self):
        """选择用户"""
        users = self.auth.read_users()
        if not users:
            print("❌ 错误：未找到可用账号，请先编辑config/users.txt文件")
            sys.exit(1)

        if len(users) == 1:
            # 只有一个用户，直接使用
            print(f"📱 使用唯一账号: {users[0]['email']}")
            return users[0]['num']

        while True:
            try:
                choice_input = input("\n✏️ 请选择要使用的账号序号: ").strip()

                if not choice_input:
                    # 用户按回车，使用第一个账号
                    return users[0]['num']

                choice = int(choice_input)
                selected_user = next((u for u in users if u['num'] == choice), None)
                if selected_user:
                    return choice
                print("❌ 无效的序号，请重新选择")
            except ValueError:
                print("❌ 请输入数字")
            except KeyboardInterrupt:
                print("\n👋 程序退出")
                sys.exit(0)

    def _get_valid_cookie(self):
        """获取有效的Cookie，如果过期则尝试重新登录"""
        # 首先尝试获取现有Cookie
        cookie = self.auth.get_cookie(self.user_id)

        if cookie:
            print(f"✅ 使用已保存的Cookie (用户ID: {self.user_id})")
            return cookie

        # Cookie无效或过期，尝试重新登录
        print(f"⚠️ 用户 {self.user_id} 的Cookie无效或已过期，正在尝试重新登录...")

        try:
            self.auth.login(self.user_id)
            # 重新获取Cookie
            cookie = self.auth.get_cookie(self.user_id)
            if cookie:
                print(f"✅ 重新登录成功，已获取新的Cookie")
                return cookie
            else:
                print(f"❌ 重新登录后仍无法获取Cookie")
                return None
        except Exception as e:
            print(f"❌ 重新登录失败: {str(e)}")
            return None

    def get_response(self, url, retry=Config.RETRY_COUNT):
        """获取网页响应，带重试功能"""
        for attempt in range(retry + 1):
            try:
                resp = self.session.get(url)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                self.logger.warning(f"第{attempt+1}次请求失败: {url}, 错误: {str(e)}")
                if attempt < retry:
                    wait_time = Config.RETRY_DELAY * (attempt + 1)
                    self.logger.info(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"请求失败，已达到最大重试次数: {url}")
                    raise Exception(f"网络请求失败，已重试{retry}次: {str(e)}")

    def get_novel_info(self, novel_id):
        """获取小说信息"""
        self.logger.info(f"获取小说信息: {novel_id}")
        url = f"{Config.BASE_URL}/novel/intro?id={novel_id}"

        try:
            soup = BeautifulSoup(self.get_response(url).content, 'html.parser')

            # 提取小说基本信息
            title = soup.select_one('div.info_box h1').text.strip()
            author_elem = soup.select_one('.info_box .item a[href*="author"]')
            author = author_elem.text.strip() if author_elem else "未知作者"

            categories = ' '.join([
                a.text.strip()
                for a in soup.select('div.info_box div.item a[href*="category"]')
            ])

            description = soup.select_one('.brief_box .txt.ellipsis').text.strip()

            tags = ' '.join([
                a.text.strip()
                for a in soup.select('.tag_box a[href*="tag"]')
            ])

            # 获取卷和章节的结构
            volumes = []
            volume_elements = soup.select('div.catalog_box li.volume')

            if volume_elements:  # 有卷结构
                for volume in volume_elements:
                    volume_title = volume.select_one('span').text.strip()
                    chapter_links = [
                        (Config.BASE_URL + a['href'], a.find(string=True, recursive=False).strip())
                        for a in volume.select('ul.children a[href]')
                    ]
                    if chapter_links:
                        volumes.append((volume_title, chapter_links))
            else:  # 无卷结构
                chapter_links = [
                    (Config.BASE_URL + a['href'], a.find(string=True, recursive=False).strip())
                    for a in soup.select('div.catalog_box a[href]')
                ]
                if chapter_links:
                    volumes.append(('', chapter_links))

            self.logger.info(f"获取小说信息成功: {title}")
            return {
                'id': novel_id,
                'title': title,
                'author': author,
                'categories': categories,
                'description': description,
                'tags': tags,
                'volumes': volumes,
                'total_chapters': sum(len(chapters) for _, chapters in volumes)
            }

        except Exception as e:
            self.logger.exception(f"获取小说信息失败: {str(e)}")
            raise Exception(f"获取小说信息失败: {str(e)}")

    def download_chapter(self, url, chapter_title):
        """下载单个章节内容"""
        self.logger.info(f"下载章节: {chapter_title}")
        try:
            soup = BeautifulSoup(self.get_response(url).content, 'html.parser')
            content = soup.select_one('div.article')

            if not content:
                self.logger.warning(f"章节内容未找到: {chapter_title}")
                return f"[章节内容未找到: {chapter_title}]"

            text = '\n'.join(
                p.find(string=True, recursive=False).strip()
                for p in content.select('div.line')
                if p.find(string=True, recursive=False) and p.find(string=True, recursive=False).strip()
            )

            return text
        except Exception as e:
            self.logger.exception(f"下载章节失败: {chapter_title}, 错误: {str(e)}")
            return f"[下载失败: {str(e)}]"

    def _get_volume_info(self, chapter_num, volumes):
        """确定章节所在卷及是否为卷首章节"""
        total = 0
        for vol_index, (_, chapters) in enumerate(volumes):
            total += len(chapters)
            if chapter_num <= total:
                # 计算章节在当前卷中的位置
                chapter_in_volume = chapter_num - (total - len(chapters))
                return vol_index, chapter_in_volume == 1
        return len(volumes) - 1, False

    def download_novel(self, novel_id, start_chapter=1, end_chapter=None):
        """下载小说，可以指定起始章节和终止章节"""
        try:
            # 获取小说信息
            novel_info = self.get_novel_info(novel_id)
            title = novel_info['title']
            volumes = novel_info['volumes']
            total_chapters = novel_info['total_chapters']

            # 验证章节范围
            if start_chapter < 1:
                start_chapter = 1

            if not end_chapter or end_chapter > total_chapters:
                end_chapter = total_chapters

            if start_chapter > end_chapter:
                raise ValueError("起始章节不能大于结束章节")

            # 创建文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            output_path = Config.OUTPUT_DIR / f"{safe_title}.txt"

            print(f"\n📚 开始下载《{title}》")
            print(f"📝 作者：{novel_info['author']}")
            print(f"🏷️ 题材：{novel_info['categories']}")
            print(f"📊 下载范围：第{start_chapter}章 至 第{end_chapter}章（共{end_chapter-start_chapter+1}章）")
            print("💡 按 Ctrl+C 可随时停止下载")

            # 计算要跳过的章节数
            chapters_to_skip = start_chapter - 1
            current_chapter = 1

            # 选择写入模式
            file_mode = 'w' if start_chapter == 1 else 'a'

            try:
                with open(output_path, file_mode, encoding='utf-8') as f:
                    # 只有从第1章开始下载时才写入小说信息
                    if start_chapter == 1:
                        f.write(f"{title}\n作者：{novel_info['author']}\n题材：{novel_info['categories']}\n")
                        f.write(f"标签：{novel_info['tags']}\n\n{novel_info['description']}\n\n\n")

                    for volume_title, chapters in volumes:
                        if chapters_to_skip >= len(chapters):
                            chapters_to_skip -= len(chapters)
                            current_chapter += len(chapters)
                            continue

                        # 只在有卷标题时才进行卷标题的输出判断
                        if volume_title:
                            _, is_first_chapter = self._get_volume_info(current_chapter + chapters_to_skip, volumes)
                            if (current_chapter == 1 and start_chapter == 1) or is_first_chapter:
                                f.write(f"\n{volume_title}\n\n")

                        for i, (url, chapter_title) in enumerate(chapters):
                            if chapters_to_skip > 0:
                                chapters_to_skip -= 1
                                current_chapter += 1
                                continue

                            if current_chapter > end_chapter:
                                break

                            # 下载章节内容
                            content = self.download_chapter(url, chapter_title)
                            if content:
                                f.write(f"\n{chapter_title}\n\n{content}\n\n")
                                print(f"✅ [{current_chapter}/{end_chapter}] {chapter_title}")

                                # 更新进度
                                self.progress_mgr.update_progress(
                                    novel_id, title, current_chapter + 1, total_chapters
                                )

                                # 如果还有更多章节要下载，则等待一段时间
                                if current_chapter < end_chapter:
                                    time.sleep(Config.CHAPTER_DELAY)

                            current_chapter += 1

                        if current_chapter > end_chapter:
                            break

            except KeyboardInterrupt:
                print(f"\n\n⚠️ 检测到 Ctrl+C，正在停止下载...")
                # 保存当前进度
                if current_chapter <= total_chapters:
                    self.progress_mgr.update_progress(
                        novel_id, title, current_chapter, total_chapters
                    )
                    print(f"📄 已下载内容保存在: {output_path}")
                    print("💡 下次可以选择从当前位置继续下载")
                print("👋 下载已停止")
                return

            print(f"\n✅ 下载完成！")
            print(f"📄 文件保存在: {output_path}")

            # 如果下载完所有章节，清除进度
            # if end_chapter == total_chapters:
            #     self.progress_mgr.clear_progress(novel_id)

        except KeyboardInterrupt:
            print(f"\n\n⚠️ 检测到 Ctrl+C，下载已取消")
            print("👋 程序退出")
            return
        except Exception as e:
            self.logger.exception(f"下载小说失败: {str(e)}")
            raise Exception(f"下载失败: {str(e)}")

    def interactive_download(self):
        """交互式下载小说"""
        try:
            width = 80
            print("\n" + "=" * width)
            print("\033[92m" + "📚 小说下载工具".center(width) + "\033[0m")
            print("=" * width)
            print(f"👤 当前使用账号ID: {self.user_id}")

            try:
                # 输入小说ID
                novel_id = input("✏️ 请输入小说ID: ").strip()
                if not novel_id:
                    print("❌ 小说ID不能为空")
                    return
                if novel_id.lower() == 'q':
                    print("✅ 已取消操作")
                    return

                # 获取小说信息
                print(f"🔍 正在获取小说《{novel_id}》的信息...")
                novel_info = self.get_novel_info(novel_id)

                print(f"\n📕 小说信息")
                print(f"  标题：{novel_info['title']}")
                print(f"  作者：{novel_info['author']}")
                print(f"  题材：{novel_info['categories']}")
                print(f"  总章节数：{novel_info['total_chapters']}")

                # 检查是否有下载记录
                progress = self.progress_mgr.get_novel_progress(novel_id)
                if progress:
                    print(f"\n⏱️ 已有下载记录，上次下载到第{progress['next_chapter']-1}章")
                    choice = input("✏️ 是否从上次位置继续下载？(y/n/q退出): ").strip().lower()

                    if choice == 'q':
                        print("✅ 已取消操作")
                        return
                    elif choice == 'y':
                        start_chapter = progress['next_chapter']
                    else:
                        start_input = input(f"✏️ 请输入起始章节 (1-{novel_info['total_chapters']}，输入q退出): ").strip()
                        if start_input.lower() == 'q':
                            print("✅ 已取消操作")
                            return
                        start_chapter = int(start_input) if start_input else 1
                else:
                    start_input = input(f"✏️ 请输入起始章节 (1-{novel_info['total_chapters']}，输入q退出): ").strip()
                    if start_input.lower() == 'q':
                        print("✅ 已取消操作")
                        return
                    start_chapter = int(start_input) if start_input else 1

                # 输入结束章节
                end_choice = input(f"✏️ 是否下载至最后一章？(y/n/q退出): ").strip().lower()
                if end_choice == 'q':
                    print("✅ 已取消操作")
                    return
                elif end_choice == 'y':
                    end_chapter = novel_info['total_chapters']
                else:
                    end_input = input(f"✏️ 请输入结束章节 ({start_chapter}-{novel_info['total_chapters']}，输入q退出): ").strip()
                    if end_input.lower() == 'q':
                        print("✅ 已取消操作")
                        return
                    end_chapter = int(end_input) if end_input else novel_info['total_chapters']

                # 确认下载
                print(f"\n📝 即将下载《{novel_info['title']}》第{start_chapter}章至第{end_chapter}章，共{end_chapter-start_chapter+1}章")
                confirm = input("✏️ 确认下载？(y/n): ").strip().lower()

                if confirm == 'y':
                    self.download_novel(novel_id, start_chapter, end_chapter)
                else:
                    print("❌ 已取消下载")
            except KeyboardInterrupt:
                print(f"\n\n⚠️ 程序退出")
            except ValueError as e:
                print(f"❌ 输入有误：{str(e)}")
            except Exception as e:
                print(f"❌ 下载失败：{str(e)}")

        except KeyboardInterrupt:
            print(f"\n👋 小说下载工具已退出")
