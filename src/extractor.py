"""
ImageExtractor - 图片链接提取器
从 Markdown 内容中提取在线图片引用
"""
import re
from dataclasses import dataclass
from typing import List


@dataclass
class ImageReference:
    """图片引用数据类"""
    original_text: str      # 完整的原始文本
    url: str                # 图片 URL
    alt_text: str           # alt 文本
    start_pos: int          # 起始位置
    end_pos: int            # 结束位置
    syntax_type: str        # 'markdown' | 'html'


class ImageExtractor:
    """图片链接提取器"""
    
    # Markdown 图片语法: ![alt](url) 或 ![alt](url "title")
    MD_IMAGE_PATTERN = re.compile(
        r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)',
        re.MULTILINE
    )
    
    # HTML img 标签: <img src="url"> 或 <img src='url'>
    HTML_IMAGE_PATTERN = re.compile(
        r'<img\s+[^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*>',
        re.IGNORECASE | re.MULTILINE
    )
    
    def extract_images(self, content: str) -> List[ImageReference]:
        """
        从 Markdown 内容中提取所有在线图片引用
        
        Args:
            content: Markdown 文件内容
        Returns:
            图片引用列表（仅包含 http/https URL）
        """
        images: List[ImageReference] = []
        
        # 提取 Markdown 格式图片
        images.extend(self._extract_markdown_images(content))
        
        # 提取 HTML 格式图片
        images.extend(self._extract_html_images(content))
        
        # 过滤：仅保留在线图片（http/https）
        images = [img for img in images if self._is_online_url(img.url)]
        
        # 按位置排序
        images.sort(key=lambda x: x.start_pos)
        
        return images
    
    def _extract_markdown_images(self, content: str) -> List[ImageReference]:
        """提取 ![alt](url) 格式的图片"""
        images: List[ImageReference] = []
        
        for match in self.MD_IMAGE_PATTERN.finditer(content):
            alt_text = match.group(1)
            url = match.group(2)
            
            images.append(ImageReference(
                original_text=match.group(0),
                url=url,
                alt_text=alt_text,
                start_pos=match.start(),
                end_pos=match.end(),
                syntax_type='markdown'
            ))
        
        return images
    
    def _extract_html_images(self, content: str) -> List[ImageReference]:
        """提取 <img src="url"> 格式的图片"""
        images: List[ImageReference] = []
        
        for match in self.HTML_IMAGE_PATTERN.finditer(content):
            url = match.group(1)
            
            # 尝试提取 alt 属性
            alt_match = re.search(r'alt\s*=\s*["\']([^"\']*)["\']', match.group(0), re.IGNORECASE)
            alt_text = alt_match.group(1) if alt_match else ''
            
            images.append(ImageReference(
                original_text=match.group(0),
                url=url,
                alt_text=alt_text,
                start_pos=match.start(),
                end_pos=match.end(),
                syntax_type='html'
            ))
        
        return images
    
    def _is_online_url(self, url: str) -> bool:
        """检查是否为在线 URL（http/https）"""
        url_lower = url.lower().strip()
        return url_lower.startswith('http://') or url_lower.startswith('https://')
