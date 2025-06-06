import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QCheckBox, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtGui import QFont, QTextCharFormat, QTextCursor, QColor
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import sys
import os
import shutil

def resource_path(relative_path):
    """适配 PyInstaller 和普通运行环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 指定运行时可写路径（首次运行会拷贝）
RUNTIME_MEMO = os.path.join(os.path.abspath("."), "memos_runtime.json")

# 如果不存在，就从只读的资源中复制一份
if not os.path.exists(RUNTIME_MEMO):
    try:
        shutil.copy(resource_path("memos.json"), RUNTIME_MEMO)
    except Exception as e:
        print("初始 JSON 复制失败：", e)

SAVE_FILE = RUNTIME_MEMO

class TodoItem(QWidget):
    def __init__(self, save_callback=None, delete_callback=None):
        super().__init__()
        self.save_callback = save_callback
        self.delete_callback = delete_callback

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
        self.textbox.setPlaceholderText("")
        self.textbox.textChanged.connect(self.adjust_textbox_height)
        self.textbox.textChanged.connect(self.save_callback)

        self.delete_button = QPushButton("🗑")
        self.delete_button.setFixedWidth(28)
        self.delete_button.setStyleSheet("QPushButton { border: none; }")
        self.delete_button.clicked.connect(self.delete_self)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.textbox)
        layout.addWidget(self.delete_button)

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
            doc_height = doc.documentLayout().documentSize().height()
            if doc_height < 5:
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
            self.save_callback()

    def delete_self(self):
        if self.delete_callback:
            self.delete_callback(self)

    def to_dict(self):
        return {
            "text": self.textbox.toPlainText(),
            "done": self.checkbox.isChecked()
        }

    def from_dict(self, data):
        text = data.get("text", "")
        if not isinstance(text, str):
            text = ''
        self.textbox.setPlainText(text)
        self.checkbox.setChecked(data.get("done", False))
        self.toggle_done(Qt.Checked if data.get("done", False) else Qt.Unchecked)
        # QTimer.singleShot(0, self.adjust_textbox_height)


class MemoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(" Reminder")
        self.resize(600, 600)
        self.setWindowIcon(QIcon("icon.ico"))
        self.setStyleSheet("QWidget { background-color: #f5f7fa; }")
        self.setWindowOpacity(0.95)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 10, 2, 2)
        self.layout.setSpacing(10)

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

        self.add_button = QPushButton("➕ 添加任务")
        self.add_button.setFont(QFont("微软雅黑", 12))  # 字号可调
        self.add_button.setStyleSheet("QPushButton { font-size: 24px; padding: 6px; }")
        self.add_button.clicked.connect(self.add_todo_item)
        self.layout.addWidget(self.add_button)

        self.load_memos()

        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;  /* 和桌面颜色融合 */
                border: none;
            }
        """)

    def add_todo_item(self, text="", done=False):
        item = TodoItem(save_callback=self.save_memos, delete_callback=self.delete_todo_item)
        item.from_dict({"text": text, "done": done})
        self.scroll_layout.addWidget(item)
        self._adjust_scroll_area_height()
        self.save_memos()

    def delete_todo_item(self, item):
        item.setParent(None)
        item.deleteLater()
        self._adjust_scroll_area_height()
        self.save_memos()

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
                    self.add_todo_item(item_data.get("text", ""), item_data.get("done", False))
            except Exception as e:
                print("加载失败：", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MemoApp()
    window.show()
    sys.exit(app.exec_())
