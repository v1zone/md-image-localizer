"""
MDScanner - Markdown 文件扫描器
递归扫描目录中的所有 .md 文件
"""
import os
from typing import List


class MDScanner:
    """Markdown 文件扫描器"""
    
    def scan_directory(self, root_path: str) -> List[str]:
        """
        递归扫描目录，返回所有 .md 文件路径列表
        
        Args:
            root_path: 根目录路径
        Returns:
            所有 Markdown 文件的绝对路径列表
        Raises:
            ValueError: 如果路径不存在或不是目录
        """
        if not os.path.exists(root_path):
            raise ValueError(f"路径不存在: {root_path}")
        
        if not os.path.isdir(root_path):
            raise ValueError(f"路径不是目录: {root_path}")
        
        md_files: List[str] = []
        
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                if filename.lower().endswith('.md'):
                    full_path = os.path.abspath(os.path.join(dirpath, filename))
                    md_files.append(full_path)
        
        return md_files
