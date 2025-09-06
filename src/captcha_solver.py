import base64
import json
import requests
import io
from PIL import Image
from .config import Config
from .logger import setup_logger

class CaptchaSolver:
    """验证码识别器"""

    def __init__(self):
        self.logger = setup_logger('captcha')
        self.api_url = Config.AI_API_BASE_URL
        self.api_key = Config.AI_API_KEY

        if not self.api_key:
            raise ValueError("请在config.py中配置AI_API_KEY")

    def solve_captcha(self, image_element, driver):
        """
        识别验证码
        Args:
            image_element: 验证码图片元素
            driver: WebDriver实例
        Returns:
            str: 识别结果
        """
        try:
            # 截取验证码图片
            image_data = self._capture_captcha_image(image_element, driver)

            # 转换为base64
            base64_image = self._image_to_base64(image_data)

            # 调用AI API识别
            result = self._call_ai_api(base64_image)

            self.logger.info(f"验证码识别结果: {result}")
            return result

        except Exception as e:
            self.logger.exception(f"验证码识别失败: {str(e)}")
            raise

    def _capture_captcha_image(self, image_element, driver):
        """截取验证码图片"""
        try:
            # 获取图片位置和大小
            location = image_element.location
            size = image_element.size

            # 截取整个页面
            screenshot = driver.get_screenshot_as_png()

            # 使用PIL处理图片
            image = Image.open(io.BytesIO(screenshot))

            # 裁剪验证码区域
            left = location['x']
            top = location['y']
            right = left + size['width']
            bottom = top + size['height']

            captcha_image = image.crop((left, top, right, bottom))

            return captcha_image

        except Exception as e:
            self.logger.exception(f"截取验证码图片失败: {str(e)}")
            raise

    def _image_to_base64(self, image):
        """将PIL图片转换为base64"""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            return base64_string

        except Exception as e:
            self.logger.exception(f"图片转换base64失败: {str(e)}")
            raise

    def _call_ai_api(self, base64_image):
        """调用AI API识别验证码"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                "model": Config.AI_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "这是一个数学验证码图片，请识别图片中的数学算式并计算结果。只返回最终的数字答案，不要包含其他文字。例如：如果图片显示'5-0×9=?'，你应该返回'5'。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content'].strip()

                # 提取数字结果
                import re
                numbers = re.findall(r'-?\d+', answer)
                if numbers:
                    return numbers[0]
                else:
                    return answer
            else:
                self.logger.error(f"AI API请求失败: {response.status_code} - {response.text}")
                raise Exception(f"AI API请求失败: {response.status_code}")

        except Exception as e:
            self.logger.exception(f"调用AI API失败: {str(e)}")
            raise
