import json
import re
import sys
import time
import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from .config import Config
from .logger import setup_logger
from .captcha_solver import CaptchaSolver

class AuthManager:
    """身份验证管理类"""

    def __init__(self):
        """初始化身份验证管理器"""
        self.logger = setup_logger('auth')
        self.cookie_file = Config.COOKIE_FILE
        self.users_file = Config.USERS_FILE
        self.captcha_solver = CaptchaSolver()

        # 确保数据目录存在
        Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def read_users(self):
        """从用户文件中读取账号信息"""
        try:
            if not self.users_file.exists():
                self.logger.error(f"用户文件不存在：{self.users_file}")
                print(f"❌ 错误：用户文件不存在，请先运行 'python main.py setup'")
                return []

            with open(self.users_file, 'r', encoding='utf-8') as f:
                users = []
                for line in f:
                    # 跳过注释行和空行
                    if line.strip().startswith('#') or not line.strip():
                        continue

                    match = re.match(r'(\d+)\.\s+(\S+)\s+(\S+)', line.strip())
                    if match:
                        num, email, password = match.groups()
                        users.append({
                            'num': int(num),
                            'email': email.strip(),
                            'password': password.strip()
                        })

                return users
        except Exception as e:
            self.logger.exception(f"读取用户文件时出错: {str(e)}")
            return []

    def _get_chromedriver_path(self):
        """获取ChromeDriver路径，自动下载和管理"""
        self.logger.info("开始获取ChromeDriver...")
        print("🔄 正在检查/下载ChromeDriver...")

        try:
            # 确保目录存在
            Config.WEBDRIVER_CACHE_DIR.mkdir(parents=True, exist_ok=True)

            # 使用webdriver_manager自动管理ChromeDriver
            self.logger.info("使用webdriver_manager自动管理ChromeDriver")

            # 设置webdriver_manager的缓存目录为项目目录
            os.environ['WDM_LOCAL'] = '1'  # 启用本地缓存
            os.environ['WDM_LOG'] = str(logging.NOTSET)  # 减少日志输出

            # 下载/获取ChromeDriver
            chromedriver_path = ChromeDriverManager().install()
            self.logger.info(f"ChromeDriver下载成功: {chromedriver_path}")
            print(f"✅ ChromeDriver下载成功: {chromedriver_path}")

            return chromedriver_path

        except Exception as e:
            self.logger.warning(f"webdriver_manager失败: {str(e)}")
            print(f"⚠️ 自动下载ChromeDriver失败: {str(e)}")

            # 下载失败
            self.logger.error("无法获取ChromeDriver")
            print("❌ 错误: 无法获取ChromeDriver，请尝试以下解决方案：")
            print("  1. 检查网络连接")
            print("  2. 确保Chrome浏览器已正确安装")
            print("  3. 检查防火墙设置")
            sys.exit(1)

    def login(self, user_id=None):
        """登录并获取Cookie"""
        try:
            users = self.read_users()
            if not users:
                self.logger.error("没有可用的账号")
                print("❌ 错误：未找到可用账号，请先编辑config/users.txt文件")
                sys.exit(1)

            # 处理 "all" 参数，为所有用户登录
            if user_id == "all":
                self.logger.info("开始为所有用户登录")
                print(f"\n🔑 开始为所有 {len(users)} 个账号登录...")

                success_count = 0
                failed_users = []

                for i, user in enumerate(users, 1):
                    print(f"\n{'='*50}")
                    print(f"正在处理第 {i}/{len(users)} 个账号: {user['email']}")
                    print(f"{'='*50}")

                    # 检查该用户的Cookie是否已存在且有效
                    existing_cookie = self.get_cookie(user['num'])
                    if existing_cookie:
                        print(f"✅ 账号 {user['email']} 的Cookie仍然有效，跳过登录")
                        self.logger.info(f"用户 {user['num']} 的Cookie有效，跳过登录")
                        success_count += 1
                        continue

                    try:
                        self._selenium_login(user)
                        success_count += 1
                        print(f"✅ 账号 {user['email']} 登录成功")
                    except KeyboardInterrupt:
                        print(f"\n👋 登录已取消，程序退出")
                        sys.exit(0)
                    except Exception as e:
                        self.logger.error(f"账号 {user['email']} 登录失败: {str(e)}")
                        print(f"❌ 账号 {user['email']} 登录失败: {str(e)}")
                        failed_users.append(user['num'])

                    # 在账号之间添加短暂延迟
                    if i < len(users):
                        print("⏳ 等待 3 秒后继续下一个账号...")
                        time.sleep(3)

                # 显示总结
                print(f"\n{'='*50}")
                print(f"📊 登录完成统计:")
                print(f"  ✅ 成功/跳过: {success_count}/{len(users)}")
                print(f"  ❌ 失败: {len(failed_users)}/{len(users)}")
                if failed_users:
                    print(f"  ❌ 失败账号: {', '.join(map(str, failed_users))}")
                print(f"{'='*50}")

                return

            # 选择用户
            selected_user = None
            if user_id:
                # 尝试将 user_id 转换为整数
                try:
                    user_id_int = int(user_id)
                    selected_user = next((u for u in users if u['num'] == user_id_int), None)
                    if not selected_user:
                        self.logger.error(f"未找到编号为{user_id_int}的用户")
                        print(f"❌ 错误：未找到编号为{user_id_int}的用户")
                        sys.exit(1)
                except ValueError:
                    self.logger.error(f"无效的用户ID: {user_id}")
                    print(f"❌ 错误：无效的用户ID: {user_id}")
                    sys.exit(1)
            else:
                # 显示可用账号让用户选择
                print("\n📝 可用账号列表：")
                for user in users:
                    # 检查Cookie状态
                    cookie_status = ""
                    existing_cookie = self.get_cookie(user['num'])
                    if existing_cookie:
                        cookie_status = " [Cookie有效]"
                    else:
                        cookie_status = " [需要登录]"
                    print(f"  {user['num']}. {user['email']}{cookie_status}")

                while True:
                    try:
                        choice = int(input("\n✏️ 请选择要使用的账号序号: "))
                        selected_user = next((u for u in users if u['num'] == choice), None)
                        if selected_user:
                            break
                        print("❌ 无效的序号，请重新选择")
                    except ValueError:
                        print("❌ 请输入数字")
                    except KeyboardInterrupt:
                        print("\n👋 登录已取消")
                        sys.exit(0)

            # 检查选中用户的Cookie是否已存在且有效
            existing_cookie = self.get_cookie(selected_user['num'])
            if existing_cookie:
                print(f"✅ 账号 {selected_user['email']} 的Cookie仍然有效，无需重新登录")
                self.logger.info(f"用户 {selected_user['num']} 的Cookie有效，跳过登录")
                return

            # 登录获取Cookie
            self._selenium_login(selected_user)

        except KeyboardInterrupt:
            print("\n👋 登录管理器已退出")
            sys.exit(0)

    def _save_user_cookie(self, user, cookie_data):
        """保存用户Cookie，支持多用户管理"""
        try:
            # 读取现有的cookies文件
            existing_cookies = []
            if self.cookie_file.exists():
                try:
                    with open(self.cookie_file, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                        if isinstance(content, list):
                            existing_cookies = content
                except json.JSONDecodeError:
                    self.logger.warning("Cookie文件格式错误，将创建新文件")
                    existing_cookies = []

            # 查找是否已存在该用户的Cookie
            user_found = False
            for i, existing_cookie in enumerate(existing_cookies):
                if existing_cookie.get('user_id') == user['num']:
                    # 用户已存在，覆盖
                    existing_cookies[i] = cookie_data
                    user_found = True
                    self.logger.info(f"更新用户 {user['num']} 的Cookie")
                    print(f"✅ 用户 {user['num']} 的Cookie已更新")
                    break

            if not user_found:
                # 用户不存在，追加
                existing_cookies.append(cookie_data)
                self.logger.info(f"添加用户 {user['num']} 的Cookie")
                print(f"✅ 用户 {user['num']} 的Cookie已添加")

            # 按user_id排序
            existing_cookies.sort(key=lambda x: x.get('user_id', 0))

            # 保存更新后的cookies
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(existing_cookies, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.logger.exception(f"保存Cookie时出错: {str(e)}")
            print(f"❌ 保存Cookie时出错: {str(e)}")
            return False

    def _selenium_login(self, user):
        """使用Selenium模拟登录获取Cookie"""
        self.logger.info(f"开始登录: {user['email']}")
        print(f"\n🔑 开始使用账号 {user['email']} 登录...")

        # 配置Chrome选项
        chrome_options = Options()
        for option, value in Config.CHROME_OPTIONS.items():
            if isinstance(value, bool) and value:
                chrome_options.add_argument(f"--{option.replace('_', '-')}")
            elif isinstance(value, str):
                chrome_options.add_argument(f"--{option.replace('_', '-')}={value}")

        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.set_capability('acceptInsecureCerts', True)

        # 获取ChromeDriver路径
        chromedriver_path = self._get_chromedriver_path()

        try:
            service = Service(executable_path=chromedriver_path)

            # 启动浏览器
            driver = webdriver.Chrome(service=service, options=chrome_options)
            wait = WebDriverWait(driver, 15)  # 增加等待时间

            try:
                # 访问首页
                driver.get(Config.BASE_URL)

                # 等待页面加载完成（等待登录按钮出现）
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".enroll_box")))

                # 点击登录按钮打开登录界面
                login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".enroll_box a[onclick*='code: 1']")))
                login_btn.click()

                # 等待登录框出现
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login_box")))

                # 输入邮箱和密码
                email_input = wait.until(EC.presence_of_element_located((By.NAME, "login_name")))
                email_input.clear()
                email_input.send_keys(user['email'])

                password_input = wait.until(EC.presence_of_element_located((By.NAME, "login_password")))
                password_input.clear()
                password_input.send_keys(user['password'])

                # 处理验证码
                print("🔍 正在识别验证码...")
                captcha_image = wait.until(EC.presence_of_element_located((By.ID, "login_captche_img")))

                max_captcha_attempts = 3
                for attempt in range(max_captcha_attempts):
                    try:
                        # 等待验证码图片加载完成
                        time.sleep(1)

                        # 识别验证码
                        captcha_result = self.captcha_solver.solve_captcha(captcha_image, driver)
                        print(f"🤖 验证码识别结果: {captcha_result}")

                        # 输入验证码
                        captcha_input = wait.until(EC.presence_of_element_located((By.NAME, "check_code")))
                        captcha_input.clear()
                        captcha_input.send_keys(captcha_result)

                        # 点击登录按钮
                        submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "login_btn")))
                        submit_button.click()

                        # 等待登录结果
                        time.sleep(2)

                        # 检查是否登录成功（有token cookie）
                        token_cookie = driver.get_cookie('token')
                        if token_cookie:
                            print("✅ 登录成功！")
                            break
                        else:
                            # 登录失败，可能是验证码错误，刷新验证码重试
                            if attempt < max_captcha_attempts - 1:
                                print(f"❌ 验证码可能错误，正在重试 ({attempt + 1}/{max_captcha_attempts})...")
                                refresh_btn = driver.find_element(By.CSS_SELECTOR, ".captcha_box .refresh")
                                refresh_btn.click()
                                time.sleep(1)
                            else:
                                raise Exception("验证码识别失败次数过多")

                    except Exception as e:
                        if attempt < max_captcha_attempts - 1:
                            print(f"❌ 验证码处理失败，正在重试 ({attempt + 1}/{max_captcha_attempts}): {str(e)}")
                            # 刷新验证码
                            try:
                                refresh_btn = driver.find_element(By.CSS_SELECTOR, ".captcha_box .refresh")
                                refresh_btn.click()
                                time.sleep(1)
                            except:
                                pass
                        else:
                            raise

                # 获取所需的Cookie
                token_cookie = driver.get_cookie('token')

                if token_cookie:
                    self.logger.info("获取Cookie成功")
                    print("\n✅ Cookie获取成功！")

                    # 将cookies转换为Header String格式
                    cookies = driver.get_cookies()
                    cookie_string = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

                    # 保存Cookie
                    cookie_data = {
                        'user_id': user['num'],
                        'user_email': user['email'],
                        'token': token_cookie['value'],
                        'Cookie': cookie_string,
                        'timestamp': datetime.now().timestamp(),
                        'expires': token_cookie.get('expiry', None),
                        'expires_date': datetime.fromtimestamp(token_cookie['expiry']).strftime('%Y-%m-%d %H:%M:%S') if 'expiry' in token_cookie else None
                    }

                    self._save_user_cookie(user, cookie_data)

                    print(f"✅ Cookie已保存，有效期至 {cookie_data.get('expires_date', '未知')}")

                else:
                    self.logger.error("获取Cookie失败")
                    print("❌ 获取Cookie失败")

            except TimeoutException:
                self.logger.error("页面加载超时")
                print("❌ 页面加载超时，请检查网络连接或尝试其他账号")
                sys.exit(1)

            except Exception as e:
                self.logger.exception(f"登录过程中出错: {str(e)}")
                print(f"❌ 登录过程中出错: {str(e)}")
                sys.exit(1)

            finally:
                driver.quit()

        except WebDriverException as e:
            self.logger.exception(f"启动浏览器时出错: {str(e)}")
            print(f"\n❌ 启动浏览器时出错: {str(e)}")
            print("\n❌ 错误: 无法启动浏览器，请确认：")
            print("  1. Chrome 浏览器已正确安装")
            print("  2. 网络连接正常（用于下载ChromeDriver）")
            print("  3. 系统防火墙或杀毒软件未阻止程序运行")
            sys.exit(1)

    def get_cookie(self, user_id=None):
        """获取Cookie字符串，支持多用户查找"""
        try:
            if not self.cookie_file.exists():
                self.logger.error("Cookie文件不存在")
                return None

            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                content = json.load(f)

            if not isinstance(content, list):
                self.logger.error("Cookie文件格式不正确，需要数组格式")
                return None

            cookies_list = content

            # 如果指定了user_id，查找特定用户
            if user_id is not None:
                for cookie_data in cookies_list:
                    if cookie_data.get('user_id') == user_id:
                        validated_cookie = self._validate_cookie(cookie_data)
                        if validated_cookie:
                            return validated_cookie
                        else:
                            return None

                return None
            else:
                # 如果没有指定user_id，返回第一个有效的Cookie
                for cookie_data in cookies_list:
                    validated_cookie = self._validate_cookie(cookie_data)
                    if validated_cookie:
                        return validated_cookie

                return None

        except Exception as e:
            self.logger.exception(f"获取Cookie时出错: {str(e)}")
            return None

    def _validate_cookie(self, cookie_data):
        """验证Cookie是否有效"""
        try:
            # 检查Cookie是否过期
            if 'expires' in cookie_data and cookie_data['expires']:
                expires = datetime.fromtimestamp(cookie_data['expires'])
                if expires < datetime.now():
                    self.logger.warning(f"用户 {cookie_data.get('user_id', 'Unknown')} 的Cookie已过期")
                    return None

            # 检查必要字段是否存在
            if 'Cookie' not in cookie_data:
                self.logger.warning(f"用户 {cookie_data.get('user_id', 'Unknown')} 的Cookie数据不完整")
                return None

            # 返回Cookie字符串
            return cookie_data['Cookie']

        except Exception as e:
            self.logger.exception(f"验证Cookie时出错: {str(e)}")
            return None
