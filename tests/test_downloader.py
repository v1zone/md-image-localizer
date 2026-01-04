"""
ImageDownloader 属性测试
Property 5: 文件名生成唯一性
Property 6: 扩展名保持
Property 7: URL 缓存复用
Validates: Requirements 4.2, 4.3, 4.4, 4.5, 4.6, 4.8
"""
import os
import sys
import tempfile
from hypothesis import given, strategies as st, settings, assume
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.downloader import ImageDownloader


# 生成有效的文件名部分
def valid_filename_part():
    return st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=15
    )


# 生成图片扩展名
def image_extension():
    return st.sampled_from(['.png', '.jpg', '.jpeg', '.gif', '.webp'])


# 生成在线 URL
def online_url_with_filename():
    return st.builds(
        lambda protocol, domain, path, name, ext: f"{protocol}://{domain}.com/{path}/{name}{ext}",
        protocol=st.sampled_from(['http', 'https']),
        domain=valid_filename_part(),
        path=valid_filename_part(),
        name=valid_filename_part(),
        ext=image_extension()
    )


# 生成无文件名的 URL
def online_url_without_filename():
    return st.builds(
        lambda protocol, domain, path: f"{protocol}://{domain}.com/{path}/",
        protocol=st.sampled_from(['http', 'https']),
        domain=valid_filename_part(),
        path=valid_filename_part()
    )


class TestImageDownloaderProperties:
    """ImageDownloader 属性测试"""
    
    # Feature: md-image-localizer, Property 5: 文件名生成唯一性
    # Validates: Requirements 4.3, 4.4, 4.5
    @given(
        urls=st.lists(online_url_with_filename(), min_size=2, max_size=10, unique=True)
    )
    @settings(max_examples=100)
    def test_filename_uniqueness(self, urls):
        """
        Property 5: 文件名生成唯一性
        对于任意一组 URL，生成的本地文件名应该互不相同
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            generated_filenames = []
            
            for url in urls:
                # 使用空内容测试文件名生成
                filename = downloader._generate_filename(url, '', b'')
                generated_filenames.append(filename)
                # 模拟文件已存在
                downloader._existing_files.add(filename)
            
            # 验证唯一性
            assert len(generated_filenames) == len(set(generated_filenames)), \
                f"文件名不唯一: {generated_filenames}"
    
    # Feature: md-image-localizer, Property 5 (续): 优先使用原始文件名
    # Validates: Requirements 4.3
    @given(
        name=valid_filename_part(),
        ext=image_extension(),
        domain=valid_filename_part()
    )
    @settings(max_examples=100)
    def test_original_filename_preferred(self, name, ext, domain):
        """
        Property 5 (续): 当不冲突时，优先使用原始文件名
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            url = f"https://{domain}.com/images/{name}{ext}"
            filename = downloader._generate_filename(url, '', b'')
            
            # 验证使用了原始文件名
            assert filename == f"{name}{ext}", \
                f"未使用原始文件名: 期望 {name}{ext}, 实际 {filename}"
    
    # Feature: md-image-localizer, Property 5 (续): 冲突时添加哈希后缀
    # Validates: Requirements 4.4
    @given(
        name=valid_filename_part(),
        ext=image_extension(),
        domain1=valid_filename_part(),
        domain2=valid_filename_part()
    )
    @settings(max_examples=100)
    def test_hash_suffix_on_conflict(self, name, ext, domain1, domain2):
        """
        Property 5 (续): 文件名冲突时添加哈希后缀
        """
        assume(domain1 != domain2)  # 确保 URL 不同
        
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            url1 = f"https://{domain1}.com/images/{name}{ext}"
            url2 = f"https://{domain2}.com/images/{name}{ext}"
            
            # 第一个文件名
            filename1 = downloader._generate_filename(url1, '', b'')
            downloader._existing_files.add(filename1)
            
            # 第二个文件名（应该有哈希后缀）
            filename2 = downloader._generate_filename(url2, '', b'')
            
            # 验证
            assert filename1 != filename2, "冲突的文件名应该不同"
            assert filename1 == f"{name}{ext}", "第一个应该是原始文件名"
            assert name in filename2 and ext in filename2, "第二个应该包含原始名称和扩展名"
            assert '_' in filename2, "第二个应该包含哈希后缀分隔符"
    
    # Feature: md-image-localizer, Property 6: 扩展名保持
    # Validates: Requirements 4.2, 4.6
    @given(
        name=valid_filename_part(),
        ext=image_extension(),
        domain=valid_filename_part()
    )
    @settings(max_examples=100)
    def test_extension_preserved(self, name, ext, domain):
        """
        Property 6: 扩展名保持
        如果 URL 包含有效扩展名，生成的文件名应该保留该扩展名
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            url = f"https://{domain}.com/images/{name}{ext}"
            filename = downloader._generate_filename(url, '', b'')
            
            # 验证扩展名保持
            assert filename.endswith(ext), \
                f"扩展名未保持: 期望以 {ext} 结尾, 实际 {filename}"
    
    # Feature: md-image-localizer, Property 6 (续): 从内容检测扩展名
    # Validates: Requirements 4.6
    def test_extension_detection_from_content(self):
        """
        Property 6 (续): 无法从 URL 获取扩展名时，根据内容检测
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            # PNG 魔数
            png_magic = b'\x89PNG\r\n\x1a\n'
            url = "https://example.com/image"  # 无扩展名
            
            filename = downloader._generate_filename(url, '', png_magic + b'\x00' * 100)
            
            assert filename.endswith('.png'), \
                f"未能从内容检测 PNG 扩展名: {filename}"
    
    # Feature: md-image-localizer, Property 7: URL 缓存复用
    # Validates: Requirements 4.8
    @given(
        url=online_url_with_filename()
    )
    @settings(max_examples=100)
    def test_url_cache_reuse(self, url):
        """
        Property 7: URL 缓存复用
        多次请求同一 URL 应该返回相同的本地路径
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            # 模拟已下载
            filename = downloader._generate_filename(url, '', b'')
            local_path = os.path.join(tmpdir, filename)
            downloader.url_to_local[url] = local_path
            
            # 再次请求
            result = downloader.download_image(url)
            
            # 验证返回缓存的路径
            assert result.success is True
            assert result.local_path == local_path


class TestImageDownloaderUnit:
    """ImageDownloader 单元测试"""
    
    def test_assets_folder_creation(self):
        """测试 assets 目录自动创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assets_path = os.path.join(tmpdir, 'new_assets')
            assert not os.path.exists(assets_path)
            
            downloader = ImageDownloader(assets_path)
            
            assert os.path.exists(assets_path)
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            # 测试非法字符
            assert downloader._sanitize_filename('file<>:name') == 'file___name'
            assert downloader._sanitize_filename('file/name') == 'file_name'
            
            # 测试空文件名
            assert downloader._sanitize_filename('') == 'image'
    
    def test_short_hash(self):
        """测试短哈希生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            hash1 = downloader._short_hash('url1')
            hash2 = downloader._short_hash('url2')
            
            # 哈希长度为 6
            assert len(hash1) == 6
            assert len(hash2) == 6
            
            # 不同输入产生不同哈希
            assert hash1 != hash2
            
            # 相同输入产生相同哈希
            assert downloader._short_hash('url1') == hash1
    
    def test_extract_filename_from_url(self):
        """测试从 URL 提取文件名"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            # 正常 URL
            name, ext = downloader._extract_filename_from_url(
                'https://example.com/images/photo.png'
            )
            assert name == 'photo'
            assert ext == '.png'
            
            # URL 编码
            name, ext = downloader._extract_filename_from_url(
                'https://example.com/images/%E5%9B%BE%E7%89%87.jpg'
            )
            assert name == '图片'
            assert ext == '.jpg'
            
            # 无扩展名
            name, ext = downloader._extract_filename_from_url(
                'https://example.com/images/photo'
            )
            assert name == 'photo'
            assert ext is None
    
    def test_content_type_detection(self):
        """测试 Content-Type 扩展名检测"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(tmpdir)
            
            # 无 URL 扩展名，使用 Content-Type
            url = "https://example.com/image"
            ext = downloader._detect_extension(b'', url, 'image/png')
            assert ext == '.png'
            
            ext = downloader._detect_extension(b'', url, 'image/jpeg; charset=utf-8')
            assert ext == '.jpg'
