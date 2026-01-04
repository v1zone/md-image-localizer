"""
MDScanner 属性测试
Property 1: 目录扫描完整性
Validates: Requirements 2.1
"""
import os
import tempfile
import shutil
from hypothesis import given, strategies as st, settings
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scanner import MDScanner


class TestMDScannerProperties:
    """MDScanner 属性测试"""
    
    # Feature: md-image-localizer, Property 1: 目录扫描完整性
    # Validates: Requirements 2.1
    @given(
        md_files=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=97, max_codepoint=122),
                min_size=1,
                max_size=10
            ),
            min_size=0,
            max_size=5
        ),
        other_files=st.lists(
            st.tuples(
                st.text(
                    alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=97, max_codepoint=122),
                    min_size=1,
                    max_size=10
                ),
                st.sampled_from(['.txt', '.py', '.json', '.html', '.css'])
            ),
            min_size=0,
            max_size=5
        ),
        subdirs=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('L', 'N'), min_codepoint=97, max_codepoint=122),
                min_size=1,
                max_size=8
            ),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=100)
    def test_scan_returns_only_md_files(self, md_files, other_files, subdirs):
        """
        Property 1: 目录扫描完整性
        对于任意目录结构，扫描结果应该：
        - 包含所有 .md 文件
        - 不包含任何非 .md 文件
        - 每个路径都是有效的绝对路径
        """
        scanner = MDScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            created_md_files = set()
            
            # 创建根目录下的 .md 文件
            for i, name in enumerate(md_files):
                if name:  # 确保文件名非空
                    filename = f"{name}_{i}.md"
                    filepath = os.path.join(tmpdir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('# Test')
                    created_md_files.add(os.path.abspath(filepath))
            
            # 创建根目录下的非 .md 文件
            for i, (name, ext) in enumerate(other_files):
                if name:
                    filename = f"{name}_{i}{ext}"
                    filepath = os.path.join(tmpdir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('test content')
            
            # 创建子目录及其中的文件
            for i, subdir_name in enumerate(subdirs):
                if subdir_name:
                    subdir_path = os.path.join(tmpdir, f"{subdir_name}_{i}")
                    os.makedirs(subdir_path, exist_ok=True)
                    
                    # 在子目录中创建 .md 文件
                    md_filename = f"sub_{i}.md"
                    md_filepath = os.path.join(subdir_path, md_filename)
                    with open(md_filepath, 'w', encoding='utf-8') as f:
                        f.write('# Subdir Test')
                    created_md_files.add(os.path.abspath(md_filepath))
                    
                    # 在子目录中创建非 .md 文件
                    other_filepath = os.path.join(subdir_path, f"other_{i}.txt")
                    with open(other_filepath, 'w', encoding='utf-8') as f:
                        f.write('other content')
            
            # 执行扫描
            result = scanner.scan_directory(tmpdir)
            result_set = set(result)
            
            # 验证属性
            # 1. 所有返回的文件都是 .md 文件
            for path in result:
                assert path.lower().endswith('.md'), f"非 .md 文件被包含: {path}"
            
            # 2. 所有返回的路径都是绝对路径
            for path in result:
                assert os.path.isabs(path), f"路径不是绝对路径: {path}"
            
            # 3. 所有创建的 .md 文件都被找到
            assert created_md_files == result_set, \
                f"缺少文件: {created_md_files - result_set}, 多余文件: {result_set - created_md_files}"


class TestMDScannerUnit:
    """MDScanner 单元测试"""
    
    def test_empty_directory(self):
        """测试空目录"""
        scanner = MDScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scanner.scan_directory(tmpdir)
            assert result == []
    
    def test_nonexistent_path(self):
        """测试不存在的路径"""
        scanner = MDScanner()
        with pytest.raises(ValueError, match="路径不存在"):
            scanner.scan_directory("/nonexistent/path/12345")
    
    def test_file_path_instead_of_directory(self):
        """测试传入文件路径而非目录"""
        scanner = MDScanner()
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b'# Test')
            filepath = f.name
        
        try:
            with pytest.raises(ValueError, match="路径不是目录"):
                scanner.scan_directory(filepath)
        finally:
            os.unlink(filepath)
    
    def test_case_insensitive_extension(self):
        """测试扩展名大小写不敏感"""
        scanner = MDScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建不同大小写扩展名的文件
            extensions = ['.md', '.MD', '.Md', '.mD']
            for i, ext in enumerate(extensions):
                filepath = os.path.join(tmpdir, f"test{i}{ext}")
                with open(filepath, 'w') as f:
                    f.write('# Test')
            
            result = scanner.scan_directory(tmpdir)
            assert len(result) == 4
