import re
import sys
from pathlib import Path
from .config import Config
from .logger import setup_logger

class ChapterModifier:
    """章节编号修改工具类"""

    def __init__(self):
        """初始化章节修改器"""
        self.logger = setup_logger('modifier')

    def modify_chapters(self, filepath, start_chapter, end_chapter, increment):
        """修改章节编号"""
        try:
            self.logger.info(f"开始修改章节编号: {filepath}, 范围: {start_chapter}-{end_chapter}, 增量: {increment}")

            # 读取文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用正则表达式匹配"第XXX章"并在指定区间内修改数字
            def replace_chapter(match):
                num = int(match.group(1))
                if start_chapter <= num <= end_chapter:
                    return f"第{num + increment}章"
                return match.group(0)

            # 替换所有匹配项
            modified_content = re.sub(r'第(\d+)章', replace_chapter, content)

            # 写回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            operation = "增加" if increment > 0 else "减少"
            print(f"✅ 已成功将第{start_chapter}章到第{end_chapter}章的章节编号{operation}{abs(increment)}。")
            self.logger.info(f"章节修改完成: {filepath}")
            return True

        except Exception as e:
            self.logger.exception(f"修改章节编号失败: {str(e)}")
            print(f"❌ 修改章节编号失败: {str(e)}")
            return False

    def modify_chapters_by_name(self, filepath, start_chapter_name, end_chapter_name, increment):
        """通过章节名修改章节编号"""
        try:
            self.logger.info(f"开始按章节名修改: {filepath}, 开始: {start_chapter_name}, 结束: {end_chapter_name}, 增量: {increment}")

            # 读取文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找所有章节并记录其位置、编号和名称
            chapter_pattern = r'第(\d+)章\s+(.+?)(?=\n|$)'
            chapters = []

            for match in re.finditer(chapter_pattern, content):
                chapters.append({
                    'start': match.start(),
                    'end': match.end(),
                    'num': int(match.group(1)),
                    'name': match.group(2).strip(),
                    'full_match': match.group(0)
                })

            if not chapters:
                print("❌ 文件中未找到章节格式")
                return False

            # 查找开始和结束章节的位置索引（按文档顺序）
            start_index = None
            end_index = None

            clean_start = re.sub(r'[^\w\u4e00-\u9fff]', '', start_chapter_name)
            clean_end = re.sub(r'[^\w\u4e00-\u9fff]', '', end_chapter_name)

            for i, chapter in enumerate(chapters):
                clean_name = re.sub(r'[^\w\u4e00-\u9fff]', '', chapter['name'])

                if clean_name == clean_start and start_index is None:
                    start_index = i
                    print(f"\n🔍 找到开始章节: 第{chapter['num']}章 {chapter['name']} (位置: {i+1})")

                if clean_name == clean_end:
                    end_index = i
                    print(f"🔍 找到结束章节: 第{chapter['num']}章 {chapter['name']} (位置: {i+1})")

            # 验证找到的章节
            if start_index is None:
                print(f"❌ 未找到包含\"{start_chapter_name}\"的章节")
                return False

            if end_index is None:
                print(f"❌ 未找到包含\"{end_chapter_name}\"的章节")
                return False

            if start_index > end_index:
                print("❌ 开始章节在文档中的位置不能晚于结束章节")
                return False

            # 确定要修改的章节范围（按文档位置）
            chapters_to_modify = chapters[start_index:end_index+1]
            print(f"📝 将修改从位置 {start_index+1} 到位置 {end_index+1} 的章节，共 {len(chapters_to_modify)} 章")

            # 显示将要修改的章节
            print("\n📖 将要修改的章节：")
            for i, chapter in enumerate(chapters_to_modify):
                new_num = chapter['num'] + increment
                print(f"  第{chapter['num']}章 → 第{new_num}章 {chapter['name']}")

            # 询问用户是否确认修改
            operation = "增加" if increment > 0 else "减少"
            confirm = input(f"\n✏️ 确认{operation}{abs(increment)}个章节编号？(y/n): ").strip().lower()

            if confirm != 'y':
                print("❌ 已取消修改操作")
                return False

            # 从后往前替换，避免位置偏移问题
            modified_content = content
            for chapter in reversed(chapters_to_modify):
                new_num = chapter['num'] + increment
                new_chapter_text = f"第{new_num}章 {chapter['name']}"
                modified_content = (
                    modified_content[:chapter['start']] +
                    new_chapter_text +
                    modified_content[chapter['end']:]
                )

            # 写回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            print(f"\n✅ 已成功将指定范围内的 {len(chapters_to_modify)} 个章节编号{operation}{abs(increment)}。")
            self.logger.info(f"按章节名修改完成: {filepath}")
            return True

        except Exception as e:
            self.logger.exception(f"按章节名修改失败: {str(e)}")
            print(f"❌ 按章节名修改失败: {str(e)}")
            return False

    def interactive_modify(self):
        """交互式修改章节编号"""
        width = 80
        print("\n" + "=" * width)
        print("\033[92m" + "📝 章节编号修改工具".center(width) + "\033[0m")
        print("=" * width)

        # 显示可用的小说文件
        print("\n可用小说文件:")
        novels = list(Config.OUTPUT_DIR.glob("*.txt"))

        if not novels:
            print("❌ 没有找到小说文件，请先下载小说")
            return

        for i, novel in enumerate(novels):
            print(f"{i+1}. {novel.name}")
        print("0. 取消并退出")

        # 选择文件
        while True:
            try:
                choice = input("\n✏️ 请选择要修改的文件序号: ").strip()
                if not choice:
                    print("❌ 未输入任何内容，请重新选择")
                    continue

                choice = int(choice)
                if choice == 0:
                    print("✅ 已取消操作")
                    return
                elif 1 <= choice <= len(novels):
                    filepath = novels[choice-1]
                    break
                else:
                    print("❌ 无效的序号，请重新选择")
            except ValueError:
                print("❌ 请输入数字")

        # 选择修改模式
        print("\n📝 请选择修改模式：")
        print("  1. 按章节编号修改")
        print("  2. 按章节名称修改（推荐）")
        print("  0. 返回上级菜单")

        try:
            mode_choice = input("\n✏️ 请选择模式 (0-2): ").strip()

            if mode_choice == '0':
                print("✅ 已取消操作")
                return
            elif mode_choice == '1':
                # 按编号修改
                start_chapter = int(input("✏️ 请输入开始章节数: "))
                end_chapter = int(input("✏️ 请输入结束章节数: "))
                increment = int(input("✏️ 请输入章节修改值(+/-数字): "))

                if start_chapter > end_chapter:
                    print("❌ 开始章节不能大于结束章节!")
                    return

                self.modify_chapters(filepath, start_chapter, end_chapter, increment)

            elif mode_choice == '2':
                # 按章节名修改
                start_name = input("✏️ 请输入开始章节名称: ").strip()
                if not start_name:
                    print("❌ 开始章节名称不能为空")
                    return

                end_name = input("✏️ 请输入结束章节名称: ").strip()
                if not end_name:
                    print("❌ 结束章节名称不能为空")
                    return

                increment = int(input("✏️ 请输入章节修改值(+/-数字): "))

                self.modify_chapters_by_name(filepath, start_name, end_name, increment)

            else:
                print("❌ 无效的选择")

        except ValueError as e:
            print(f"❌ 请输入有效的数字! {str(e)}")
        except KeyboardInterrupt:
            print("\n✅ 已取消操作")

class ExtractScriptGenerator:
    """章节提取脚本生成器"""

    def __init__(self):
        """初始化脚本生成器"""
        self.logger = setup_logger('extract')

    def generate_script(self):
        """生成章节提取脚本"""
        self.logger.info("生成章节提取脚本")

        script = """function extractChapterContent() {
    // 提取章节标题
    const rawTitle = document.querySelector('h2').innerText;

    // 清理标题格式
    let chapterTitle = rawTitle
        .split('&nbsp;')
        .pop() // 获取最后一部分（章节名）
        .replace(/^第.+卷\\s*/, '') // 移除开头的卷名
        .replace(/^\\s+|\\s+$/g, ''); // 移除首尾空格

    // 提取所有非空的line div文本
    const lines = Array.from(document.querySelectorAll('.article .line'))
        .map(line => {
            // 获取直接文本内容，移除子元素
            const clone = line.cloneNode(true);
            Array.from(clone.getElementsByTagName('span')).forEach(span => span.remove());
            return clone.textContent.trim();
        })
        .filter(text => text.length > 0);  // 过滤空行

    // 组合成指定格式
    const content = lines.join('\\n');
    const output = `${chapterTitle}\\n\\n${content}\\n\\n\\n`;

    // 创建临时textarea用于复制
    const textArea = document.createElement('textarea');
    textArea.value = output;
    document.body.appendChild(textArea);

    // 在控制台显示内容
    console.log(output);

    // 复制到剪贴板
    textArea.select();
    try {
        document.execCommand('copy');
        console.log('内容已复制到剪贴板');
    } catch (err) {
        console.error('复制失败:', err);
    }

    document.body.removeChild(textArea);
}

extractChapterContent();"""

        # 保存脚本到文件
        script_path = Config.DATA_DIR / "extract_script.js"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)

        print("\n📜 章节提取脚本生成成功！")
        print(f"📄 脚本保存在: {script_path}")
        print("\n使用方法:")
        print("1. 在浏览器中打开小说章节页面")
        print("2. 按F12打开开发者工具")
        print("3. 切换到Console/控制台标签")
        print("4. 复制上面生成的脚本内容，粘贴到控制台中并运行")
        print("5. 章节内容会自动复制到剪贴板")
