"""
ImageDownloader - 图片下载器
下载在线图片到本地并生成唯一文件名
"""
import os
import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, unquote
import requests


@dataclass
class DownloadResult:
    """下载结果数据类"""
    success: bool
    url: str
    local_path: str         # 下载成功时的本地路径
    error_message: str      # 失败时的错误信息


class ImageDownloader:
    """图片下载器"""
    
    # 支持的图片扩展名
    VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'}
    
    # 图片魔数（magic bytes）用于检测格式
    MAGIC_BYTES = {
        b'\x89PNG\r\n\x1a\n': '.png',
        b'\xff\xd8\xff': '.jpg',
        b'GIF87a': '.gif',
        b'GIF89a': '.gif',
        b'RIFF': '.webp',  # WebP 以 RIFF 开头
        b'<svg': '.svg',
        b'<?xml': '.svg',  # SVG 可能以 XML 声明开头
        b'BM': '.bmp',
        b'\x00\x00\x01\x00': '.ico',
    }
    
    # Content-Type 到扩展名的映射
    CONTENT_TYPE_MAP = {
        'image/png': '.png',
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'image/svg+xml': '.svg',
        'image/bmp': '.bmp',
        'image/x-icon': '.ico',
        'image/vnd.microsoft.icon': '.ico',
    }
    
    def __init__(self, assets_folder: str):
        """
        初始化下载器
        
        Args:
            assets_folder: 存放下载图片的目录
        """
        self.assets_folder = assets_folder
        self.url_to_local: Dict[str, str] = {}  # URL 到本地路径的映射缓存
        self._existing_files: set = set()  # 已存在的文件名集合
        
        # 确保目录存在
        os.makedirs(assets_folder, exist_ok=True)
        
        # 加载已存在的文件
        if os.path.exists(assets_folder):
            self._existing_files = set(os.listdir(assets_folder))
    
    def download_image(self, url: str, timeout: int = 30) -> DownloadResult:
        """
        下载单张图片到本地
        
        Args:
            url: 图片 URL
            timeout: 超时时间（秒）
        Returns:
            下载结果
        """
        # 检查缓存
        if url in self.url_to_local:
            return DownloadResult(
                success=True,
                url=url,
                local_path=self.url_to_local[url],
                error_message=""
            )
        
        try:
            # 下载图片
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            content = response.content
            content_type = response.headers.get('Content-Type', '')
            
            # 生成文件名
            filename = self._generate_filename(url, content_type, content)
            local_path = os.path.join(self.assets_folder, filename)
            
            # 保存文件
            with open(local_path, 'wb') as f:
                f.write(content)
            
            # 更新缓存
            self.url_to_local[url] = local_path
            self._existing_files.add(filename)
            
            return DownloadResult(
                success=True,
                url=url,
                local_path=local_path,
                error_message=""
            )
            
        except requests.exceptions.Timeout:
            return DownloadResult(
                success=False,
                url=url,
                local_path="",
                error_message=f"下载超时: {url}"
            )
        except requests.exceptions.RequestException as e:
            return DownloadResult(
                success=False,
                url=url,
                local_path="",
                error_message=f"下载失败: {str(e)}"
            )
        except Exception as e:
            return DownloadResult(
                success=False,
                url=url,
                local_path="",
                error_message=f"未知错误: {str(e)}"
            )
    
    def _generate_filename(self, url: str, content_type: str, content: bytes = None) -> str:
        """
        生成本地文件名
        优先使用原始文件名，冲突时添加哈希后缀
        
        Args:
            url: 图片 URL
            content_type: HTTP 响应的 Content-Type
            content: 图片内容（用于检测格式）
        Returns:
            唯一的本地文件名
        """
        # 从 URL 提取原始文件名
        original_name, original_ext = self._extract_filename_from_url(url)
        
        # 确定扩展名
        extension = self._detect_extension(content, url, content_type)
        if not extension:
            extension = original_ext or '.bin'
        
        # 确定基础文件名
        if original_name:
            base_name = original_name
        else:
            # 无法提取文件名，使用 URL 哈希
            base_name = self._short_hash(url)
        
        # 清理文件名（移除非法字符）
        base_name = self._sanitize_filename(base_name)
        
        # 检查冲突并生成唯一文件名
        filename = f"{base_name}{extension}"
        
        if filename not in self._existing_files:
            return filename
        
        # 文件名冲突，添加哈希后缀
        hash_suffix = self._short_hash(url)
        filename = f"{base_name}_{hash_suffix}{extension}"
        
        # 极端情况：仍然冲突（理论上不太可能）
        counter = 1
        while filename in self._existing_files:
            filename = f"{base_name}_{hash_suffix}_{counter}{extension}"
            counter += 1
        
        return filename
    
    def _extract_filename_from_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从 URL 提取文件名和扩展名
        
        Returns:
            (文件名不含扩展名, 扩展名) 或 (None, None)
        """
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path)
            
            # 获取路径最后一部分
            filename = os.path.basename(path)
            
            if not filename:
                return None, None
            
            # 分离文件名和扩展名
            name, ext = os.path.splitext(filename)
            ext_lower = ext.lower()
            
            if ext_lower in self.VALID_EXTENSIONS:
                return name if name else None, ext_lower
            
            return name if name else None, None
            
        except Exception:
            return None, None
    
    def _detect_extension(self, content: bytes, url: str, content_type: str) -> Optional[str]:
        """
        检测图片扩展名
        优先级：URL > Content-Type > 内容检测
        """
        # 1. 从 URL 提取
        _, ext = self._extract_filename_from_url(url)
        if ext:
            return ext
        
        # 2. 从 Content-Type 提取
        if content_type:
            ct_lower = content_type.lower().split(';')[0].strip()
            if ct_lower in self.CONTENT_TYPE_MAP:
                return self.CONTENT_TYPE_MAP[ct_lower]
        
        # 3. 从内容检测
        if content:
            for magic, ext in self.MAGIC_BYTES.items():
                if content.startswith(magic):
                    return ext
            
            # 特殊处理 WebP（RIFF....WEBP）
            if content[:4] == b'RIFF' and len(content) >= 12 and content[8:12] == b'WEBP':
                return '.webp'
        
        return None
    
    def _short_hash(self, text: str) -> str:
        """生成短哈希值（6位）"""
        return hashlib.md5(text.encode()).hexdigest()[:6]
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除 Windows 和 Unix 不允许的字符
        illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(illegal_chars, '_', filename)
        
        # 限制长度
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        # 确保不为空
        if not sanitized:
            sanitized = 'image'
        
        return sanitized
