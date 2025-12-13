from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox,
    QSplitter, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsLineItem, QGraphicsRectItem
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QWheelEvent, QPainter
import sys
from pathlib import Path

from tiny_parser import TinyParser


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.zoom_factor = 1.15

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)


class TreeVisualizer:
    def __init__(self, scene):
        self.scene = scene
        self.horizontal_spacing = 160
        self.vertical_spacing = 100
        self.rect_width = 100
        self.rect_height = 40
        self.oval_width = 90
        self.oval_height = 50

    def draw_tree(self, ast_root):
        self.scene.clear()
        if ast_root:
            if str(ast_root.label).startswith('Program') and ast_root.children:
                root = ast_root.children[0]
            else:
                root = ast_root
            self._calculate_width(root)
            self._draw_node_or_siblings(root, 400, 50, None)

    def _calculate_width(self, node):
        if node is None:
            return 0
        
        label = str(node.label)
        
        if label.startswith('StmtSeq'):
            total_width = 0
            for child in node.children:
                total_width += self._calculate_width(child)
            node._width = max(1, total_width)
            return node._width
        
        if label.startswith('OpExpr') and len(node.children) >= 3:
            op_node = node.children[0]
            left_node = node.children[1]
            right_node = node.children[2]
            
            width = self._calculate_width(left_node) + 1 + self._calculate_width(right_node)
            node._width = width
            return width
        
        if not node.children:
            node._width = 1
            return 1
        
        total_width = 0
        for child in node.children:
            total_width += self._calculate_width(child)
        
        node._width = max(1, total_width)
        return node._width

    def _draw_node_or_siblings(self, node, x, y, parent_pos):
        if node is None:
            return 0
        
        label = str(node.label)
        
        if label.startswith('StmtSeq'):
            if not node.children:
                return 0
            
            total_width = sum(getattr(child, '_width', 1) for child in node.children)
            current_x = x - (total_width - 1) * self.horizontal_spacing / 2
            
            prev_sibling_pos = None
            for i, child in enumerate(node.children):
                child_width = getattr(child, '_width', 1)
                child_x = current_x + (child_width - 1) * self.horizontal_spacing / 2
                
                if i == 0:
                    prev_sibling_pos = self._draw_node_or_siblings(child, child_x, y, parent_pos)
                else:
                    current_pos = self._draw_node_or_siblings(child, child_x, y, None)
                    
                    if prev_sibling_pos and current_pos:
                        self._draw_sibling_pointer(prev_sibling_pos, current_pos, node.children[i-1], child)
                    prev_sibling_pos = current_pos
                
                current_x += child_width * self.horizontal_spacing
            return prev_sibling_pos
        
        if label.startswith('OpExpr') and len(node.children) >= 3:
            op_node = node.children[0]
            left_node = node.children[1]
            right_node = node.children[2]
            
            op_label = self._format_label(str(op_node.label), op_node)
            center_x = x
            center_y = y + self.oval_height / 2
            
            self._draw_shape(x, y, op_label, False, parent_pos, center_y)
            
            left_width = getattr(left_node, '_width', 1)
            right_width = getattr(right_node, '_width', 1)
            total_width = left_width + right_width
            
            left_x = x - (total_width - 1) * self.horizontal_spacing / 2
            right_x = x + (total_width - 1) * self.horizontal_spacing / 2
            child_y = y + self.oval_height + self.vertical_spacing
            
            self._draw_node_or_siblings(left_node, left_x, child_y, QPointF(center_x, y + self.oval_height))
            self._draw_node_or_siblings(right_node, right_x, child_y, QPointF(center_x, y + self.oval_height))
            return {'pos': QPointF(center_x, center_y), 'node': node, 'is_statement': False}
        
        is_statement = self._is_statement(label)
        display_label = self._format_label(label, node)
        
        if is_statement:
            height = self.rect_height
            width = self.rect_width
        else:
            height = self.oval_height
            width = self.oval_width
        
        center_x = x
        center_y = y + height / 2
        
        self._draw_shape(x, y, display_label, is_statement, parent_pos, center_y)
        
        children_to_draw = self._get_children_to_draw(node, label)
        
        if children_to_draw:
            total_width = sum(getattr(child, '_width', 1) for child in children_to_draw)
            current_x = x - (total_width - 1) * self.horizontal_spacing / 2
            child_y = y + height + self.vertical_spacing
            
            for child in children_to_draw:
                child_width = getattr(child, '_width', 1)
                child_x = current_x + (child_width - 1) * self.horizontal_spacing / 2
                self._draw_node_or_siblings(child, child_x, child_y, QPointF(center_x, y + height))
                current_x += child_width * self.horizontal_spacing
        
        return {'pos': QPointF(center_x, center_y), 'node': node, 'is_statement': is_statement}

    def _draw_sibling_pointer(self, from_info, to_info, from_node, to_node):
        from_pos = from_info['pos']
        to_pos = to_info['pos']
        from_is_statement = from_info['is_statement']
        to_is_statement = to_info['is_statement']
        
        from_width = self.rect_width if from_is_statement else self.oval_width
        from_edge_x = from_pos.x() + from_width / 2
        
        to_width = self.rect_width if to_is_statement else self.oval_width
        to_edge_x = to_pos.x() - to_width / 2
        
        line = QGraphicsLineItem(from_edge_x, from_pos.y(), to_edge_x, to_pos.y())
        pen = QPen(QColor(100, 100, 100))
        pen.setWidth(2)
        line.setPen(pen)
        line.setZValue(-1)
        self.scene.addItem(line)

    def _draw_shape(self, x, y, display_label, is_statement, parent_pos, center_y):
        if is_statement:
            width = self.rect_width
            height = self.rect_height
        else:
            width = self.oval_width
            height = self.oval_height
        
        center_x = x
        
        if parent_pos:
            line = QGraphicsLineItem(parent_pos.x(), parent_pos.y(), center_x, y)
            pen = QPen(QColor(100, 100, 100))
            pen.setWidth(2)
            line.setPen(pen)
            line.setZValue(-1)
            self.scene.addItem(line)
        
        color = QColor(173, 216, 230, 180)
        
        if is_statement:
            rect = QGraphicsRectItem(x - width/2, y, width, height)
            rect.setBrush(QBrush(color))
            rect.setPen(QPen(QColor(70, 70, 70), 2))
            rect.setZValue(0)
            self.scene.addItem(rect)
        else:
            ellipse = QGraphicsEllipseItem(x - width/2, y, width, height)
            ellipse.setBrush(QBrush(color))
            ellipse.setPen(QPen(QColor(70, 70, 70), 2))
            ellipse.setZValue(0)
            self.scene.addItem(ellipse)
        
        text = QGraphicsTextItem(display_label)
        text.setDefaultTextColor(QColor(0, 0, 0))
        font = QFont("Arial", 9, QFont.Bold)
        text.setFont(font)
        
        text_rect = text.boundingRect()
        text.setPos(
            center_x - text_rect.width() / 2,
            center_y - text_rect.height() / 2
        )
        text.setZValue(1)
        self.scene.addItem(text)

    def _get_children_to_draw(self, node, label):
        if label.startswith('ReadStmt'):
            return [child for child in node.children if not str(child.label).startswith('Identifier')]
        elif label.startswith('AssignStmt'):
            return node.children[1:] if len(node.children) > 1 else []
        return node.children

    def _format_label(self, label, node):
        if label.startswith('IfStmt'):
            return 'if'
        elif label.startswith('RepeatStmt'):
            return 'repeat'
        elif label.startswith('AssignStmt'):
            if node.children and str(node.children[0].label).startswith('Identifier('):
                var_name = str(node.children[0].label).split('(')[1].rstrip(')')
                return f'assign\n({var_name})'
            return 'assign'
        elif label.startswith('ReadStmt'):
            if node.children and str(node.children[0].label).startswith('Identifier('):
                var_name = str(node.children[0].label).split('(')[1].rstrip(')')
                return f'read\n({var_name})'
            return 'read'
        elif label.startswith('WriteStmt'):
            return 'write'
        elif label.startswith('Identifier('):
            var_name = label.split('(')[1].rstrip(')')
            return f'id\n({var_name})'
        elif label.startswith('Number('):
            num = label.split('(')[1].rstrip(')')
            return f'Const \n({num})'
        elif label.startswith('Op('):
            op = label.split('(')[1].rstrip(')')
            return f'Op\n({op})'
        return label

    def _is_statement(self, label):
        statement_types = ['IfStmt', 'RepeatStmt', 'AssignStmt', 'ReadStmt', 'WriteStmt']
        return any(label.startswith(stmt) for stmt in statement_types)


class FullScreenTreeWindow(QMainWindow):
    def __init__(self, ast_root, parent=None):
        super().__init__(parent)
        self.ast_root = ast_root
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("TINY Syntax Tree - Full Screen")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.tree_view = ZoomableGraphicsView()
        self.tree_scene = QGraphicsScene()
        self.tree_view.setScene(self.tree_scene)
        layout.addWidget(self.tree_view)

        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        button_layout.addWidget(reset_btn)
        
        zoom_fit_btn = QPushButton("Zoom to Fit")
        zoom_fit_btn.clicked.connect(self.zoom_to_fit)
        button_layout.addWidget(zoom_fit_btn)
        
        close_btn = QPushButton("Close Full Screen")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.draw_tree()

    def draw_tree(self):
        visualizer = TreeVisualizer(self.tree_scene)
        visualizer.draw_tree(self.ast_root)
        self.zoom_to_fit()

    def reset_view(self):
        self.tree_view.resetTransform()
        self.zoom_to_fit()

    def zoom_to_fit(self):
        self.tree_view.fitInView(
            self.tree_scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()


class TinyParserGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.ast_root = None
        self.fullscreen_window = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("TINY Language Parser")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Token File")
        self.load_btn.clicked.connect(self.load_file)
        
        self.parse_btn = QPushButton("Parse")
        self.parse_btn.clicked.connect(self.parse_tokens)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_all)
        
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.parse_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)

        main_splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("Token Input:"))
        self.token_input = QTextEdit()
        self.token_input.setPlaceholderText(
            "Load a token file or paste tokens here...\n"
            "Format: tokenValue , tokenType\n"
            "Example:\n"
            "read , READ\n"
            "x , IDENTIFIER\n"
            ":= , ASSIGN"
        )
        self.token_input.textChanged.connect(self.on_token_input_changed)
        left_layout.addWidget(self.token_input)
        
        main_splitter.addWidget(left_widget)

        right_splitter = QSplitter(Qt.Vertical)

        top_right_widget = QWidget()
        top_right_layout = QVBoxLayout(top_right_widget)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet(
            "color: black; font-weight: bold; padding: 8px; background-color: #f0f0f0; "
            "border-radius: 5px;"
        )
        top_right_layout.addWidget(self.status_label)

        top_right_layout.addWidget(QLabel("Parse Output:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        top_right_layout.addWidget(self.output_text)

        right_splitter.addWidget(top_right_widget)

        bottom_right_widget = QWidget()
        bottom_right_layout = QVBoxLayout(bottom_right_widget)

        tree_header_layout = QHBoxLayout()
        tree_header_layout.addWidget(QLabel("Syntax Tree:"))
        
        self.fullscreen_btn = QPushButton("Full Screen")
        self.fullscreen_btn.clicked.connect(self.open_fullscreen_tree)
        self.fullscreen_btn.setEnabled(False)
        self.fullscreen_btn.setMaximumWidth(120)
        tree_header_layout.addWidget(self.fullscreen_btn)
        tree_header_layout.addStretch()
        
        bottom_right_layout.addLayout(tree_header_layout)

        self.tree_view = ZoomableGraphicsView()
        self.tree_scene = QGraphicsScene()
        self.tree_view.setScene(self.tree_scene)
        
        instructions = QLabel("Mouse Wheel: Zoom  |  Left Click + Drag: Pan")
        instructions.setStyleSheet(
            "color: #666; font-size: 10px; padding: 3px;"
        )
        bottom_right_layout.addWidget(instructions)
        bottom_right_layout.addWidget(self.tree_view)

        right_splitter.addWidget(bottom_right_widget)

        right_splitter.setSizes([200, 600])

        main_splitter.addWidget(right_splitter)

        main_splitter.setSizes([300, 1100])
        
        main_layout.addWidget(main_splitter)

    def on_token_input_changed(self):
        has_text = bool(self.token_input.toPlainText().strip())
        self.parse_btn.setEnabled(has_text)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Token File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            return

        try:
            path = Path(file_path)
            if not path.exists():
                QMessageBox.critical(
                    self,
                    "File Error",
                    f"File does not exist:\n{file_path}"
                )
                return

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                QMessageBox.warning(
                    self,
                    "Empty File",
                    "The selected file is empty."
                )
                return

            self.token_input.setText(content)
            self.current_file = file_path
            self.parse_btn.setEnabled(True)
            self.status_label.setText(f"Status: Loaded {path.name}")
            self.status_label.setStyleSheet(
                "color: blue; font-weight: bold; padding: 8px; "
                "background-color: #e3f2fd; border-radius: 5px;"
            )
            
        except PermissionError:
            QMessageBox.critical(
                self,
                "Permission Error",
                f"Permission denied accessing file:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Error loading file:\n{str(e)}"
            )

    def parse_tokens(self):
        token_text = self.token_input.toPlainText().strip()

        if not token_text:
            QMessageBox.warning(
                self,
                "No Input",
                "Please load a token file or enter tokens manually."
            )
            return

        try:
            tokens = self.read_tokens_from_text(token_text)
            
            if not tokens:
                QMessageBox.warning(
                    self,
                    "No Valid Tokens",
                    "No valid tokens found in input."
                )
                return

            if tokens[-1][1] != 'EOF':
                tokens.append(('EOF', 'EOF'))

            parser = TinyParser(tokens)
            self.ast_root = parser.parse_program()

            self.status_label.setText("✅ Status: ACCEPTED - Valid TINY program")
            self.status_label.setStyleSheet(
                "color: white; background-color: #4caf50; font-weight: bold; "
                "padding: 8px; border-radius: 5px;"
            )
                
            output = " The input is ACCEPTED by the TINY language.\n\n"
            output += "Abstract Syntax Tree \n"
            output += str(self.ast_root)
            
            self.output_text.setText(output)

            visualizer = TreeVisualizer(self.tree_scene)
            visualizer.draw_tree(self.ast_root)
            self.tree_view.fitInView(self.tree_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
            self.fullscreen_btn.setEnabled(True)

        except Exception as e:
            self.status_label.setText("❌ Status: REJECTED - Syntax error")
            self.status_label.setStyleSheet(
                "color: white; background-color: #f44336; font-weight: bold; "
                "padding: 8px; border-radius: 5px;"
            )
            
            error_output = "The input is REJECTED by the TINY language.\n\n"
            error_output += f"Error: {str(e)}\n"
            
            self.output_text.setText(error_output)
            self.tree_scene.clear()
            self.fullscreen_btn.setEnabled(False)
            
            QMessageBox.critical(
                self,
                "Parse Error",
                f"Syntax Error:\n{str(e)}"
            )

    def read_tokens_from_text(self, text):
        tokens = []
        lines = text.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) != 2:
                raise Exception(
                    f"Invalid token format on line {line_num}:\n'{line}'\n"
                    f"Expected format: tokenValue , tokenType"
                )
            
            token_value = parts[0].strip()
            token_type = parts[1].strip()
            tokens.append((token_value, token_type))

        return tokens

    def open_fullscreen_tree(self):
        if self.ast_root:
            self.fullscreen_window = FullScreenTreeWindow(self.ast_root, self)
            self.fullscreen_window.show()

    def clear_all(self):
        self.token_input.clear()
        self.output_text.clear()
        self.tree_scene.clear()
        self.status_label.setText("Status: Ready")
        self.status_label.setStyleSheet(
            "color: black; font-weight: bold; padding: 8px; background-color: #f0f0f0; "
            "border-radius: 5px;"
        )
        self.current_file = None
        self.ast_root = None
        self.parse_btn.setEnabled(False)
        self.fullscreen_btn.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TinyParserGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()