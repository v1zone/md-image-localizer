"""
ImageExtractor 属性测试
Property 2: Markdown 图片语法提取
Property 3: HTML 图片标签提取
Property 4: URL 过滤正确性
Validates: Requirements 3.1, 3.2, 3.3, 3.4
"""
import os
import sys
from hypothesis import given, strategies as st, settings, assume
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extractor import ImageExtractor, ImageReference


# 生成有效的 URL 路径部分
def valid_url_path():
    return st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=20
    )


# 生成图片扩展名
def image_extension():
    return st.sampled_from(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'])


# 生成在线 URL
def online_url():
    return st.builds(
        lambda protocol, domain, path, ext: f"{protocol}://{domain}.com/{path}{ext}",
        protocol=st.sampled_from(['http', 'https']),
        domain=valid_url_path(),
        path=valid_url_path(),
        ext=image_extension()
    )


# 生成本地路径
def local_path():
    return st.builds(
        lambda prefix, path, ext: f"{prefix}{path}{ext}",
        prefix=st.sampled_from(['./images/', '../assets/', '/absolute/path/', 'relative/']),
        path=valid_url_path(),
        ext=image_extension()
    )


# 生成 alt 文本
def alt_text():
    return st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs'), min_codepoint=32, max_codepoint=122),
        min_size=0,
        max_size=30
    ).filter(lambda x: ']' not in x and ')' not in x)


class TestImageExtractorProperties:
    """ImageExtractor 属性测试"""
    
    # Feature: md-image-localizer, Property 2: Markdown 图片语法提取
    # Validates: Requirements 3.1
    @given(
        urls=st.lists(online_url(), min_size=1, max_size=5),
        alts=st.lists(alt_text(), min_size=1, max_size=5)
    )
    @settings(max_examples=100)
    def test_markdown_image_extraction(self, urls, alts):
        """
        Property 2: Markdown 图片语法提取
        对于任意包含 ![alt](url) 格式的 Markdown 内容，
        提取器应该找到所有匹配项，且提取的 URL 与原文完全一致
        """
        extractor = ImageExtractor()
        
        # 构建 Markdown 内容
        content_parts = []
        expected_urls = []
        
        for i, url in enumerate(urls):
            alt = alts[i % len(alts)]
            content_parts.append(f"Some text before\n![{alt}]({url})\nSome text after\n")
            expected_urls.append(url)
        
        content = "\n".join(content_parts)
        
        # 提取图片
        images = extractor.extract_images(content)
        
        # 验证
        extracted_urls = [img.url for img in images]
        
        # 所有预期的 URL 都被提取
        for url in expected_urls:
            assert url in extracted_urls, f"URL 未被提取: {url}"
        
        # 所有提取的图片都是 markdown 类型
        for img in images:
            if img.url in expected_urls:
                assert img.syntax_type == 'markdown'
    
    # Feature: md-image-localizer, Property 3: HTML 图片标签提取
    # Validates: Requirements 3.2
    @given(
        urls=st.lists(online_url(), min_size=1, max_size=5),
        alts=st.lists(alt_text(), min_size=1, max_size=5),
        use_double_quotes=st.lists(st.booleans(), min_size=1, max_size=5)
    )
    @settings(max_examples=100)
    def test_html_image_extraction(self, urls, alts, use_double_quotes):
        """
        Property 3: HTML 图片标签提取
        对于任意包含 <img src="url"> 格式的内容，
        提取器应该找到所有匹配项，支持单引号和双引号
        """
        extractor = ImageExtractor()
        
        # 构建 HTML 内容
        content_parts = []
        expected_urls = []
        
        for i, url in enumerate(urls):
            alt = alts[i % len(alts)]
            quote = '"' if use_double_quotes[i % len(use_double_quotes)] else "'"
            content_parts.append(f"<p>Text</p>\n<img src={quote}{url}{quote} alt={quote}{alt}{quote}>\n")
            expected_urls.append(url)
        
        content = "\n".join(content_parts)
        
        # 提取图片
        images = extractor.extract_images(content)
        
        # 验证
        extracted_urls = [img.url for img in images]
        
        # 所有预期的 URL 都被提取
        for url in expected_urls:
            assert url in extracted_urls, f"URL 未被提取: {url}"
        
        # 所有提取的图片都是 html 类型
        for img in images:
            if img.url in expected_urls:
                assert img.syntax_type == 'html'
    
    # Feature: md-image-localizer, Property 4: URL 过滤正确性
    # Validates: Requirements 3.3, 3.4
    @given(
        online_urls=st.lists(online_url(), min_size=0, max_size=3),
        local_paths=st.lists(local_path(), min_size=0, max_size=3)
    )
    @settings(max_examples=100)
    def test_url_filtering(self, online_urls, local_paths):
        """
        Property 4: URL 过滤正确性
        提取结果应该：
        - 仅包含 http:// 或 https:// 开头的 URL
        - 不包含任何本地路径
        """
        extractor = ImageExtractor()
        
        # 构建混合内容
        content_parts = []
        
        for url in online_urls:
            content_parts.append(f"![online]({url})")
        
        for path in local_paths:
            content_parts.append(f"![local]({path})")
        
        content = "\n".join(content_parts)
        
        # 提取图片
        images = extractor.extract_images(content)
        
        # 验证：所有提取的 URL 都是在线 URL
        for img in images:
            url_lower = img.url.lower()
            assert url_lower.startswith('http://') or url_lower.startswith('https://'), \
                f"非在线 URL 被包含: {img.url}"
        
        # 验证：所有在线 URL 都被提取
        extracted_urls = {img.url for img in images}
        for url in online_urls:
            assert url in extracted_urls, f"在线 URL 未被提取: {url}"
        
        # 验证：本地路径不被提取
        for path in local_paths:
            assert path not in extracted_urls, f"本地路径被错误提取: {path}"


class TestImageExtractorUnit:
    """ImageExtractor 单元测试"""
    
    def test_empty_content(self):
        """测试空内容"""
        extractor = ImageExtractor()
        result = extractor.extract_images("")
        assert result == []
    
    def test_no_images(self):
        """测试无图片内容"""
        extractor = ImageExtractor()
        content = "# Title\n\nSome text without images.\n\n- List item"
        result = extractor.extract_images(content)
        assert result == []
    
    def test_markdown_with_title(self):
        """测试带 title 的 Markdown 图片"""
        extractor = ImageExtractor()
        content = '![alt](https://example.com/image.png "Image Title")'
        result = extractor.extract_images(content)
        assert len(result) == 1
        assert result[0].url == "https://example.com/image.png"
    
    def test_mixed_content(self):
        """测试混合内容"""
        extractor = ImageExtractor()
        content = """
# Document

![md image](https://example.com/md.png)

Some text here.

<img src="https://example.com/html.jpg" alt="html image">

![local](./local/image.png)
"""
        result = extractor.extract_images(content)
        
        # 应该只有 2 个在线图片
        assert len(result) == 2
        
        urls = {img.url for img in result}
        assert "https://example.com/md.png" in urls
        assert "https://example.com/html.jpg" in urls
    
    def test_position_tracking(self):
        """测试位置追踪"""
        extractor = ImageExtractor()
        content = "Start ![alt](https://example.com/img.png) End"
        result = extractor.extract_images(content)
        
        assert len(result) == 1
        img = result[0]
        
        # 验证位置
        assert content[img.start_pos:img.end_pos] == img.original_text
