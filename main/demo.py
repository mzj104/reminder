import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QCheckBox, QPushButton, QScrollArea, QFrame
)
from PyQt5.QtGui import QFont, QTextCharFormat, QTextCursor, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame  # 记得 import
from PyQt5.QtCore import QTimer

def resource_path(relative_path):
    """适配 PyInstaller 打包后路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

SAVE_FILE = resource_path("memos.json")

class TodoItem(QWidget):
    def __init__(self,save_callback=None):
        super().__init__()
        self.save_callback = save_callback
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.toggle_done)

        self.textbox = QTextEdit()
        self.textbox.setFont(QFont("微软雅黑", 12))
        self.textbox.setFixedHeight(30)
        self.textbox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.textbox.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
            }
        """)
        self.textbox.setPlaceholderText("")  # 去掉提示文字
        self.textbox.textChanged.connect(self.adjust_textbox_height)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.textbox)

        self.setStyleSheet("""
            QFrame {
                border: none;
                background-color: transparent;
            }
        """)

        self.adjust_textbox_height()

    def adjust_textbox_height(self):
        doc = self.textbox.document()
        margins = self.textbox.contentsMargins()

        try:
            # 优先使用 documentSize
            doc_height = doc.documentLayout().documentSize().height()
            if doc_height < 5:  # 太小就说明没准备好，fallback
                raise ValueError
        except Exception:
            font_metrics = self.textbox.fontMetrics()
            line_count = doc.blockCount()
            line_height = font_metrics.lineSpacing()
            doc_height = line_count * line_height

        total_height = int(doc_height + margins.top() + margins.bottom() + 6)
        self.textbox.setFixedHeight(total_height)

    def toggle_done(self, state):
        cursor = self.textbox.textCursor()
        cursor.select(QTextCursor.Document)
        fmt = QTextCharFormat()
        if state == Qt.Checked:
            fmt.setFontStrikeOut(True)
            fmt.setForeground(QColor("gray"))
        else:
            fmt.setFontStrikeOut(False)
            fmt.setForeground(QColor("black"))
        cursor.mergeCharFormat(fmt)
        if self.save_callback:
            print('sdf asd')
            self.save_callback()

    def to_dict(self):
        return {
            "text": self.textbox.toPlainText(),
            "done": self.checkbox.isChecked()
        }

    def from_dict(self, data):
        self.textbox.setPlainText(data.get("text", ""))
        self.checkbox.setChecked(data.get("done", False))
        self.toggle_done(Qt.Checked if data.get("done", False) else Qt.Unchecked)
        QTimer.singleShot(0, self.adjust_textbox_height)  # ✅ 延迟触发高度刷新


from PyQt5.QtWidgets import QSizePolicy

class MemoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📝 动态备忘录")
        self.resize(600, 600)
        self.setStyleSheet("QWidget { background-color: #f5f7fa; }")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_content.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)

        # 添加按钮
        self.add_button = QPushButton("➕ 添加任务")
        self.add_button.setStyleSheet("QPushButton { font-size: 14px; padding: 6px; }")
        self.add_button.clicked.connect(self.add_todo_item)
        self.layout.addWidget(self.add_button)

        self.load_memos()


    def add_todo_item(self):
        item = TodoItem(save_callback=self.save_memos)
        self.scroll_layout.addWidget(item)
        self._adjust_scroll_area_height()
        self.save_memos()


    def refresh_layout(self):
        # 清空 layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def _adjust_scroll_area_height(self):
        total_height = 0
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                total_height += widget.sizeHint().height()
        self.scroll_content.setMinimumHeight(total_height + 10)

    def save_memos(self):
        data = []
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if isinstance(widget, TodoItem):
                data.append(widget.to_dict())
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_memos(self):
        if not os.path.exists(SAVE_FILE):
            return
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for item_data in data:
                    print(item_data)
                    item = TodoItem(save_callback=self.save_memos)
                    item.from_dict(item_data)
                    self.scroll_layout.addWidget(item)
            except Exception as e:
                print("加载失败：", e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MemoApp()
    window.show()
    sys.exit(app.exec_())
