"""
LinkReplacer 属性测试
Property 8: 链接替换正确性
Property 9: 内容保持
Validates: Requirements 5.1, 5.2
"""
import os
import sys
from hypothesis import given, strategies as st, settings, assume
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.replacer import LinkReplacer
from src.extractor import ImageExtractor, ImageReference


# 生成有效的 URL 路径部分
def valid_path_part():
    return st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=15
    )


# 生成图片扩展名
def image_extension():
    return st.sampled_from(['.png', '.jpg', '.jpeg', '.gif', '.webp'])


# 生成在线 URL
def online_url():
    return st.builds(
        lambda protocol, domain, path, name, ext: f"{protocol}://{domain}.com/{path}/{name}{ext}",
        protocol=st.sampled_from(['http', 'https']),
        domain=valid_path_part(),
        path=valid_path_part(),
        ext=image_extension(),
        name=valid_path_part()
    )


# 生成本地路径
def local_path():
    return st.builds(
        lambda folder, name, ext: f"assets/{name}{ext}",
        folder=st.just('assets'),
        name=valid_path_part(),
        ext=image_extension()
    )


# 生成 alt 文本
def alt_text():
    return st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs'), min_codepoint=32, max_codepoint=122),
        min_size=0,
        max_size=20
    ).filter(lambda x: ']' not in x and ')' not in x and '"' not in x and "'" not in x)


# 生成普通文本（不包含图片语法）
def plain_text():
    return st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs', 'Po'), min_codepoint=32, max_codepoint=122),
        min_size=0,
        max_size=50
    ).filter(lambda x: '![' not in x and '<img' not in x.lower())


class TestLinkReplacerProperties:
    """LinkReplacer 属性测试"""
    
    # Feature: md-image-localizer, Property 8: 链接替换正确性
    # Validates: Requirements 5.1
    @given(
        urls=st.lists(online_url(), min_size=1, max_size=5, unique=True),
        local_paths=st.lists(local_path(), min_size=1, max_size=5),
        alts=st.lists(alt_text(), min_size=1, max_size=5)
    )
    @settings(max_examples=100)
    def test_markdown_link_replacement(self, urls, local_paths, alts):
        """
        Property 8: 链接替换正确性 (Markdown)
        替换后的内容应该包含本地路径而非原始 URL
        """
        replacer = LinkReplacer()
        extractor = ImageExtractor()
        
        # 构建 Markdown 内容
        content_parts = []
        replacements = {}
        
        for i, url in enumerate(urls):
            alt = alts[i % len(alts)]
            local = local_paths[i % len(local_paths)]
            content_parts.append(f"![{alt}]({url})")
            replacements[url] = local
        
        content = "\n\n".join(content_parts)
        
        # 提取图片
        images = extractor.extract_images(content)
        
        # 替换
        result = replacer.replace_links(content, replacements, images)
        
        # 验证：原始 URL 不再出现
        for url in urls:
            assert url not in result, f"原始 URL 仍存在: {url}"
        
        # 验证：本地路径出现
        for url in urls:
            local = replacements[url]
            assert local in result, f"本地路径未出现: {local}"
    
    # Feature: md-image-localizer, Property 8 (续): HTML 链接替换
    # Validates: Requirements 5.1
    @given(
        urls=st.lists(online_url(), min_size=1, max_size=5, unique=True),
        local_paths=st.lists(local_path(), min_size=1, max_size=5),
        alts=st.lists(alt_text(), min_size=1, max_size=5)
    )
    @settings(max_examples=100)
    def test_html_link_replacement(self, urls, local_paths, alts):
        """
        Property 8 (续): 链接替换正确性 (HTML)
        替换后的内容应该包含本地路径而非原始 URL
        """
        replacer = LinkReplacer()
        extractor = ImageExtractor()
        
        # 构建 HTML 内容
        content_parts = []
        replacements = {}
        
        for i, url in enumerate(urls):
            alt = alts[i % len(alts)]
            local = local_paths[i % len(local_paths)]
            content_parts.append(f'<img src="{url}" alt="{alt}">')
            replacements[url] = local
        
        content = "\n\n".join(content_parts)
        
        # 提取图片
        images = extractor.extract_images(content)
        
        # 替换
        result = replacer.replace_links(content, replacements, images)
        
        # 验证：原始 URL 不再出现
        for url in urls:
            assert url not in result, f"原始 URL 仍存在: {url}"
        
        # 验证：本地路径出现
        for url in urls:
            local = replacements[url]
            assert local in result, f"本地路径未出现: {local}"
    
    # Feature: md-image-localizer, Property 9: 内容保持
    # Validates: Requirements 5.2
    @given(
        prefix=plain_text(),
        suffix=plain_text(),
        url=online_url(),
        local=local_path(),
        alt=alt_text()
    )
    @settings(max_examples=100)
    def test_content_preservation(self, prefix, suffix, url, local, alt):
        """
        Property 9: 内容保持
        替换操作不应改变非图片链接部分的任何内容
        """
        replacer = LinkReplacer()
        extractor = ImageExtractor()
        
        # 构建内容
        content = f"{prefix}\n![{alt}]({url})\n{suffix}"
        
        # 提取和替换
        images = extractor.extract_images(content)
        replacements = {url: local}
        result = replacer.replace_links(content, replacements, images)
        
        # 验证：前缀和后缀保持不变
        assert result.startswith(prefix + "\n"), f"前缀被改变: 期望以 '{prefix}\\n' 开头"
        assert result.endswith("\n" + suffix), f"后缀被改变: 期望以 '\\n{suffix}' 结尾"
    
    # Feature: md-image-localizer, Property 9 (续): 空替换映射
    # Validates: Requirements 5.2
    @given(
        content=st.text(min_size=0, max_size=200)
    )
    @settings(max_examples=100)
    def test_empty_replacements_preserve_content(self, content):
        """
        Property 9 (续): 空替换映射时内容完全保持
        """
        replacer = LinkReplacer()
        
        result = replacer.replace_links(content, {}, [])
        
        assert result == content, "空替换时内容应完全保持"


class TestLinkReplacerUnit:
    """LinkReplacer 单元测试"""
    
    def test_empty_content(self):
        """测试空内容"""
        replacer = LinkReplacer()
        result = replacer.replace_links("", {}, [])
        assert result == ""
    
    def test_no_matching_urls(self):
        """测试无匹配 URL"""
        replacer = LinkReplacer()
        extractor = ImageExtractor()
        
        content = "![alt](https://example.com/image.png)"
        images = extractor.extract_images(content)
        
        # 替换映射中没有这个 URL
        result = replacer.replace_links(content, {"https://other.com/img.png": "local.png"}, images)
        
        assert result == content
    
    def test_multiple_images_same_url(self):
        """测试多个相同 URL 的图片"""
        replacer = LinkReplacer()
        extractor = ImageExtractor()
        
        url = "https://example.com/image.png"
        content = f"![alt1]({url})\n\nSome text\n\n![alt2]({url})"
        
        images = extractor.extract_images(content)
        replacements = {url: "assets/image.png"}
        
        result = replacer.replace_links(content, replacements, images)
        
        # 两处都应该被替换
        assert url not in result
        assert result.count("assets/image.png") == 2
    
    def test_mixed_markdown_and_html(self):
        """测试混合 Markdown 和 HTML"""
        replacer = LinkReplacer()
        extractor = ImageExtractor()
        
        content = """# Title

![md image](https://example.com/md.png)

Some text here.

<img src="https://example.com/html.jpg" alt="html image">
"""
        
        images = extractor.extract_images(content)
        replacements = {
            "https://example.com/md.png": "assets/md.png",
            "https://example.com/html.jpg": "assets/html.jpg"
        }
        
        result = replacer.replace_links(content, replacements, images)
        
        assert "https://example.com/md.png" not in result
        assert "https://example.com/html.jpg" not in result
        assert "assets/md.png" in result
        assert "assets/html.jpg" in result
        assert "# Title" in result
        assert "Some text here." in result
    
    def test_generate_relative_path(self):
        """测试相对路径生成"""
        replacer = LinkReplacer()
        
        # 同级目录
        md_path = "/docs/readme.md"
        img_path = "/docs/assets/image.png"
        
        relative = replacer.generate_relative_path(md_path, img_path)
        
        assert relative == "assets/image.png"
    
    def test_html_preserves_other_attributes(self):
        """测试 HTML 替换保留其他属性"""
        replacer = LinkReplacer()
        
        img = ImageReference(
            original_text='<img src="https://example.com/img.png" alt="test" class="responsive" width="100">',
            url="https://example.com/img.png",
            alt_text="test",
            start_pos=0,
            end_pos=80,
            syntax_type='html'
        )
        
        result = replacer._generate_replacement(img, "assets/img.png")
        
        # 应该保留 alt、class、width 属性
        assert 'alt="test"' in result
        assert 'class="responsive"' in result
        assert 'width="100"' in result
        assert 'src="assets/img.png"' in result
