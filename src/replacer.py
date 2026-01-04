"""
LinkReplacer - 链接替换器
将 Markdown 内容中的在线图片链接替换为本地路径
"""
import os
import re
from typing import Dict, List

from .extractor import ImageReference


class LinkReplacer:
    """链接替换器"""
    
    def replace_links(
        self,
        content: str,
        replacements: Dict[str, str],
        images: List[ImageReference]
    ) -> str:
        """
        替换 Markdown 内容中的图片链接
        
        Args:
            content: 原始 Markdown 内容
            replacements: URL 到本地路径的映射
            images: 图片引用列表（按位置排序）
        Returns:
            替换后的 Markdown 内容
        """
        if not images or not replacements:
            return content
        
        # 按位置倒序处理，避免位置偏移
        sorted_images = sorted(images, key=lambda x: x.start_pos, reverse=True)
        
        result = content
        
        for img in sorted_images:
            if img.url not in replacements:
                continue
            
            local_path = replacements[img.url]
            
            # 生成新的图片引用文本
            new_text = self._generate_replacement(img, local_path)
            
            # 替换
            result = result[:img.start_pos] + new_text + result[img.end_pos:]
        
        return result
    
    def _generate_replacement(self, img: ImageReference, local_path: str) -> str:
        """
        生成替换后的图片引用文本
        
        Args:
            img: 原始图片引用
            local_path: 本地路径
        Returns:
            新的图片引用文本
        """
        # 转换为相对路径格式（使用正斜杠）
        relative_path = local_path.replace('\\', '/')
        
        if img.syntax_type == 'markdown':
            # Markdown 格式: ![alt](path)
            return f"![{img.alt_text}]({relative_path})"
        
        elif img.syntax_type == 'html':
            # HTML 格式: 保持原有属性，只替换 src
            original = img.original_text
            
            # 替换 src 属性值
            # 支持双引号和单引号
            new_text = re.sub(
                r'src\s*=\s*["\'][^"\']+["\']',
                f'src="{relative_path}"',
                original,
                count=1
            )
            
            return new_text
        
        return img.original_text
    
    def generate_relative_path(self, md_file_path: str, local_image_path: str) -> str:
        """
        生成从 Markdown 文件到图片的相对路径
        
        Args:
            md_file_path: Markdown 文件路径
            local_image_path: 本地图片路径
        Returns:
            相对路径
        """
        md_dir = os.path.dirname(os.path.abspath(md_file_path))
        image_abs = os.path.abspath(local_image_path)
        
        # 计算相对路径
        relative = os.path.relpath(image_abs, md_dir)
        
        # 使用正斜杠（跨平台兼容）
        relative = relative.replace('\\', '/')
        
        return relative
