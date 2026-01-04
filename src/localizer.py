"""
ImageLocalizer - 主处理器
协调各组件完成图片本地化
"""
import os
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Dict

from .scanner import MDScanner
from .extractor import ImageExtractor
from .downloader import ImageDownloader, DownloadResult
from .replacer import LinkReplacer


@dataclass
class ProcessResult:
    """处理结果统计"""
    total_files: int = 0
    processed_files: int = 0
    total_images: int = 0
    downloaded_images: int = 0
    failed_images: int = 0
    skipped_images: int = 0
    errors: List[str] = field(default_factory=list)


class ImageLocalizer:
    """图片本地化主处理器"""
    
    ASSETS_FOLDER_NAME = "assets"
    
    def __init__(self, progress_callback: Optional[Callable[[str, float], None]] = None):
        """
        初始化处理器
        
        Args:
            progress_callback: 进度回调函数，参数为 (消息, 进度百分比 0-1)
        """
        self.progress_callback = progress_callback
        self.scanner = MDScanner()
        self.extractor = ImageExtractor()
        self.replacer = LinkReplacer()
    
    def process_directory(self, root_path: str) -> ProcessResult:
        """
        处理整个目录
        
        Args:
            root_path: 根目录路径
        Returns:
            处理结果统计
        """
        result = ProcessResult()
        
        # 扫描 Markdown 文件
        self._report_progress("正在扫描 Markdown 文件...", 0)
        
        try:
            md_files = self.scanner.scan_directory(root_path)
        except ValueError as e:
            result.errors.append(str(e))
            return result
        
        result.total_files = len(md_files)
        
        if not md_files:
            self._report_progress("未找到 Markdown 文件", 1.0)
            return result
        
        self._report_progress(f"找到 {len(md_files)} 个 Markdown 文件", 0.1)
        
        # 处理每个文件
        for i, md_path in enumerate(md_files):
            progress = 0.1 + (i / len(md_files)) * 0.9
            self._report_progress(f"处理: {os.path.basename(md_path)}", progress)
            
            downloaded, failed, errors = self.process_file(md_path)
            
            result.processed_files += 1
            result.downloaded_images += downloaded
            result.failed_images += failed
            result.total_images += downloaded + failed
            result.errors.extend(errors)
        
        self._report_progress("处理完成", 1.0)
        return result
    
    def process_file(self, md_path: str) -> Tuple[int, int, List[str]]:
        """
        处理单个 Markdown 文件
        
        Args:
            md_path: Markdown 文件路径
        Returns:
            (下载成功数, 失败数, 错误列表)
        """
        downloaded = 0
        failed = 0
        errors: List[str] = []
        
        try:
            # 读取文件内容
            content = self._read_file(md_path)
            if content is None:
                errors.append(f"无法读取文件: {md_path}")
                return 0, 0, errors
            
            # 提取图片链接
            images = self.extractor.extract_images(content)
            
            if not images:
                return 0, 0, errors
            
            # 创建 assets 目录
            md_dir = os.path.dirname(os.path.abspath(md_path))
            assets_folder = os.path.join(md_dir, self.ASSETS_FOLDER_NAME)
            
            # 创建下载器
            downloader = ImageDownloader(assets_folder)
            
            # 下载图片并构建替换映射
            replacements: Dict[str, str] = {}
            
            for img in images:
                result = downloader.download_image(img.url)
                
                if result.success:
                    # 生成相对路径
                    relative_path = self.replacer.generate_relative_path(
                        md_path, result.local_path
                    )
                    replacements[img.url] = relative_path
                    downloaded += 1
                else:
                    errors.append(result.error_message)
                    failed += 1
            
            # 替换链接
            if replacements:
                new_content = self.replacer.replace_links(content, replacements, images)
                
                # 保存文件
                if not self._write_file(md_path, new_content):
                    errors.append(f"无法保存文件: {md_path}")
            
        except Exception as e:
            errors.append(f"处理文件 {md_path} 时出错: {str(e)}")
        
        return downloaded, failed, errors
    
    def _read_file(self, path: str) -> Optional[str]:
        """读取文件内容，尝试多种编码"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception:
                return None
        
        return None
    
    def _write_file(self, path: str, content: str) -> bool:
        """写入文件内容"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def _report_progress(self, message: str, progress: float):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, progress)
