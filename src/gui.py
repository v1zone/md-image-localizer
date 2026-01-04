"""
ImageLocalizerGUI - 图形界面
使用 tkinter 构建简单的 GUI
"""
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from .localizer import ImageLocalizer, ProcessResult


class ImageLocalizerGUI:
    """图片本地化工具 GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MD 图片本地化工具")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置最小尺寸
        self.root.minsize(500, 400)
        
        self.selected_folder = tk.StringVar()
        self.is_processing = False
        
        self._create_widgets()
        self._configure_styles()
    
    def _configure_styles(self):
        """配置样式"""
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TLabel', padding=2)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="Markdown 图片本地化工具",
            font=('Microsoft YaHei', 14, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # 说明文字
        desc_label = ttk.Label(
            main_frame,
            text="将 Markdown 文件中的在线图片下载到本地，防止图床链接失效",
            font=('Microsoft YaHei', 9)
        )
        desc_label.pack(pady=(0, 15))
        
        # 文件夹选择区域
        folder_frame = ttk.LabelFrame(main_frame, text="选择文件夹", padding="10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 路径显示
        self.path_entry = ttk.Entry(
            folder_frame, 
            textvariable=self.selected_folder,
            state='readonly',
            width=50
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 浏览按钮
        self.browse_btn = ttk.Button(
            folder_frame,
            text="浏览...",
            command=self._select_folder
        )
        self.browse_btn.pack(side=tk.RIGHT)
        
        # 开始按钮
        self.start_btn = ttk.Button(
            main_frame,
            text="开始处理",
            command=self._start_processing,
            state=tk.DISABLED
        )
        self.start_btn.pack(pady=10)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="就绪")
        self.progress_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            state=tk.DISABLED,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部状态栏
        self.status_label = ttk.Label(
            main_frame,
            text="请选择要处理的文件夹",
            font=('Microsoft YaHei', 9)
        )
        self.status_label.pack(pady=(10, 0))
    
    def _select_folder(self):
        """打开文件夹选择对话框"""
        folder = filedialog.askdirectory(
            title="选择包含 Markdown 文件的文件夹"
        )
        
        if folder:
            # 验证路径
            if os.path.exists(folder) and os.path.isdir(folder):
                self.selected_folder.set(folder)
                self.start_btn.config(state=tk.NORMAL)
                self.status_label.config(text=f"已选择: {folder}")
                self._log(f"已选择文件夹: {folder}")
            else:
                messagebox.showerror("错误", "选择的路径无效")
    
    def _start_processing(self):
        """开始处理"""
        if self.is_processing:
            return
        
        folder = self.selected_folder.get()
        if not folder:
            messagebox.showwarning("警告", "请先选择文件夹")
            return
        
        # 禁用按钮
        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.browse_btn.config(state=tk.DISABLED)
        
        # 清空日志
        self._clear_log()
        self._log("开始处理...")
        
        # 在后台线程中运行
        thread = threading.Thread(target=self._process_in_thread, args=(folder,))
        thread.daemon = True
        thread.start()
    
    def _process_in_thread(self, folder: str):
        """在后台线程中处理"""
        try:
            localizer = ImageLocalizer(progress_callback=self._update_progress_threadsafe)
            result = localizer.process_directory(folder)
            
            # 在主线程中显示结果
            self.root.after(0, lambda: self._show_result(result))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))
        
        finally:
            self.root.after(0, self._processing_finished)
    
    def _update_progress_threadsafe(self, message: str, progress: float):
        """线程安全的进度更新"""
        self.root.after(0, lambda: self._update_progress(message, progress))
    
    def _update_progress(self, message: str, progress: float):
        """更新进度显示"""
        self.progress_label.config(text=message)
        self.progress_bar['value'] = progress * 100
        self._log(message)
    
    def _show_result(self, result: ProcessResult):
        """显示处理结果"""
        self._log("\n" + "=" * 50)
        self._log("处理完成!")
        self._log(f"扫描文件数: {result.total_files}")
        self._log(f"处理文件数: {result.processed_files}")
        self._log(f"发现图片数: {result.total_images}")
        self._log(f"下载成功: {result.downloaded_images}")
        self._log(f"下载失败: {result.failed_images}")
        
        if result.errors:
            self._log("\n错误信息:")
            for error in result.errors[:10]:  # 最多显示 10 条
                self._log(f"  - {error}")
            if len(result.errors) > 10:
                self._log(f"  ... 还有 {len(result.errors) - 10} 条错误")
        
        self._log("=" * 50)
        
        # 显示摘要对话框
        summary = f"""处理完成!

扫描文件: {result.total_files}
处理文件: {result.processed_files}
下载图片: {result.downloaded_images}
失败: {result.failed_images}"""
        
        if result.failed_images > 0:
            messagebox.showwarning("处理完成", summary)
        else:
            messagebox.showinfo("处理完成", summary)
    
    def _show_error(self, error: str):
        """显示错误"""
        self._log(f"\n错误: {error}")
        messagebox.showerror("错误", error)
    
    def _processing_finished(self):
        """处理完成后恢复界面"""
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.browse_btn.config(state=tk.NORMAL)
        self.status_label.config(text="处理完成")
    
    def _log(self, message: str):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def run(self):
        """启动 GUI 主循环"""
        self.root.mainloop()
