import os
import json
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,QHBoxLayout, QPushButton, QFileDialog,
                               QLabel, QStackedWidget, QScrollArea, QGridLayout,
                               QProgressBar, QTreeWidget, QTreeWidgetItem, QTextBrowser, QSizePolicy, QMessageBox, QSlider)
from PySide6.QtCore import Qt, QSize, QUrl, QDir
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.linkHovered.connect(self.onLinkHovered)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        print(f"acceptNavigationRequest: url={url}, type={_type}, isMainFrame={isMainFrame}")
        if url.scheme() == "file":
            return True
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return True

    def onLinkHovered(self, url):
        pass
        #print(f"Link hovered: {url}")

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        #print(f"JavaScript Console: {message}")
        if message.startswith("Link clicked:"):
            url = QUrl(message.split(": ")[1])
            QDesktopServices.openUrl(url)

class CustomWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPage(CustomWebEnginePage(self))
        self.page().loadFinished.connect(self.onLoadFinished)

    def onLoadFinished(self, ok):
        if ok:
            self.page().runJavaScript("""
                document.addEventListener('click', function(e) {
                    var target = e.target;
                    while(target) {
                        if(target.tagName === 'A') {
                            console.log('Link clicked: ' + target.href);
                            break;
                        }
                        target = target.parentElement;
                    }
                });
            """)

class CursoCard(QWidget):
    def __init__(self, curso):
        super().__init__()
        self.curso = curso
        layout = QVBoxLayout(self)

        icon_label = QLabel()
        icon_label.setPixmap(QIcon("path_to_icon.png").pixmap(QSize(50, 50)))
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        name_label = QLabel(curso['name'])
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, curso['totalArchivos'])
        progress_bar.setValue(curso['archivosVistos'])
        layout.addWidget(progress_bar)

        progress_label = QLabel(f"{curso['archivosVistos']} / {curso['totalArchivos']} progreso vistos")
        progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(progress_label)

        change_icon_btn = QPushButton("Cambiar icono")
        layout.addWidget(change_icon_btn)

        self.setFixedSize(200, 250)
        self.setStyleSheet("border-radius: 10px;")


class CustomVideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        controls_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.play_pause)
        controls_layout.addWidget(self.play_pause_button)

        self.rewind_button = QPushButton("<<")
        self.rewind_button.clicked.connect(self.rewind)
        controls_layout.addWidget(self.rewind_button)

        self.forward_button = QPushButton(">>")
        self.forward_button.clicked.connect(self.forward)
        controls_layout.addWidget(self.forward_button)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider, 1)

        self.duration_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.duration_label)

        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(60)  # Ajusta este valor según tus preferencias
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(QLabel("Vol"))
        volume_layout.addWidget(self.volume_slider)
        controls_layout.addLayout(volume_layout)

        layout.addLayout(controls_layout)

        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_button.setText("Play")
        else:
            self.media_player.play()
            self.play_pause_button.setText("Pause")

    def rewind(self):
        self.media_player.setPosition(max(0, self.media_player.position() - 5000))

    def forward(self):
        self.media_player.setPosition(min(self.media_player.duration(), self.media_player.position() + 5000))

    def set_position(self, position):
        self.media_player.setPosition(position)

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.update_duration_label()

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_duration_label()

    def update_duration_label(self):
        position = self.media_player.position()
        duration = self.media_player.duration()
        self.duration_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

    def format_time(self, ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"

    def set_source(self, url):
        self.media_player.setSource(url)

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100.0)

class CursoTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seguimiento de Cursos")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        self.setup_ui()
        self.cargar_cursos()

    def setup_ui(self):
        # Página principal de cursos
        self.cursos_page = QWidget()
        cursos_layout = QVBoxLayout(self.cursos_page)

        titulo = QLabel("Cursos disponibles")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        cursos_layout.addWidget(titulo)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        cursos_layout.addWidget(scroll_area)

        self.cursos_grid = QWidget()
        self.grid_layout = QGridLayout(self.cursos_grid)
        scroll_area.setWidget(self.cursos_grid)

        self.btn_agregar_carpeta = QPushButton("Agregar Carpeta")
        self.btn_agregar_carpeta.clicked.connect(self.agregar_carpeta)
        cursos_layout.addWidget(self.btn_agregar_carpeta)

        self.stacked_widget.addWidget(self.cursos_page)

        # Página de detalle del curso
        self.curso_detail_page = QWidget()
        curso_detail_layout = QHBoxLayout(self.curso_detail_page)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self.mostrar_archivo)
        curso_detail_layout.addWidget(self.tree_widget, 1)

        self.content_area = QStackedWidget()

        # Área de video
        self.video_widget = CustomVideoWidget()
        self.content_area.addWidget(self.video_widget)

        # Área de HTML
        self.web_view = CustomWebEngineView()
        self.content_area.addWidget(self.web_view)

        # Área de texto (para mostrar mensajes)
        self.text_browser = QTextBrowser()
        self.content_area.addWidget(self.text_browser)

        curso_detail_layout.addWidget(self.content_area, 2)

        self.stacked_widget.addWidget(self.curso_detail_page)

    def cargar_cursos(self):
        try:
            with open("cursos_data.json", "r", encoding="utf-8") as f:
                self.cursos_data = json.load(f)

            self.actualizar_grid_cursos()
        except FileNotFoundError:
            self.generar_json_cursos()

    def actualizar_grid_cursos(self):
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        for i, (curso_name, curso_data) in enumerate(self.cursos_data.items()):
            curso_card = CursoCard(curso_data)
            curso_card.mousePressEvent = lambda event, c=curso_name: self.mostrar_detalle_curso(c)
            self.grid_layout.addWidget(curso_card, i // 3, i % 3)

    def generar_json_cursos(self):
        ruta_cursos = "cursos_videos"
        self.cursos_data = {}

        for curso in os.listdir(ruta_cursos):
            ruta_curso = os.path.join(ruta_cursos, curso)
            if os.path.isdir(ruta_curso):
                total_archivos = self.contar_archivos(ruta_curso)
                self.cursos_data[curso] = {
                    "id": curso,
                    "name": curso,
                    "description": f"Descripción del curso {curso}",
                    "totalArchivos": total_archivos,
                    "archivosVistos": 0,
                    "icon": "SiNextdotjs",
                    "archivos": self.obtener_archivos(ruta_curso),
                    "progress": {},
                    "ruta": ruta_curso
                }

        with open("cursos_data.json", "w", encoding="utf-8") as f:
            json.dump(self.cursos_data, f, ensure_ascii=False, indent=2)

        self.actualizar_grid_cursos()

    def contar_archivos(self, ruta):
        total = 0
        for raiz, dirs, archivos in os.walk(ruta):
            for archivo in archivos:
                if archivo.lower().endswith(('.mp4', '.avi', '.mov', '.html')):
                    total += 1
        return total

    def obtener_archivos(self, ruta):
        archivos = {}
        for raiz, dirs, archivos_lista in os.walk(ruta):
            seccion = os.path.relpath(raiz, ruta)
            if seccion == '.':
                seccion = 'Principal'
            archivos[seccion] = []
            for archivo in archivos_lista:
                if archivo.lower().endswith(('.mp4', '.avi', '.mov', '.html')):
                    archivos[seccion].append({
                        "nombre": archivo,
                        "tipo": "video" if archivo.lower().endswith(('.mp4', '.avi', '.mov')) else "html",
                        "visto": False
                    })
            archivos[seccion] = sorted(archivos[seccion], key=lambda x: self.ordenar_clave(x['nombre']))
        return archivos

    def ordenar_clave(self, nombre):
        match = re.search(r'^(\d+)', nombre)
        if match:
            numero = int(match.group(1))
            resto = nombre[match.end():]
            return (numero, resto.lower())
        else:
            return (float('inf'), nombre.lower())

    def mostrar_detalle_curso(self, curso_name):
        self.tree_widget.clear()

        for seccion, archivos in self.cursos_data[curso_name]['archivos'].items():
            seccion_item = QTreeWidgetItem(self.tree_widget, [seccion])
            for archivo in archivos:
                icon = QIcon("path_to_html_icon.png") if archivo['tipo'] == 'html' else QIcon("path_to_video_icon.png")
                archivo_item = QTreeWidgetItem(seccion_item, [archivo['nombre']])
                archivo_item.setIcon(0, icon)
                archivo_item.setData(0, Qt.UserRole, os.path.join(self.cursos_data[curso_name]['ruta'], seccion, archivo['nombre']))

        self.stacked_widget.setCurrentWidget(self.curso_detail_page)

    def mostrar_archivo(self, item):
        ruta_archivo = item.data(0, Qt.UserRole)
        if ruta_archivo:
            if ruta_archivo.lower().endswith(('.mp4', '.avi', '.mov')):
                self.video_widget.set_source(QUrl.fromLocalFile(ruta_archivo))
                self.content_area.setCurrentWidget(self.video_widget)
                self.video_widget.media_player.play()
            elif ruta_archivo.lower().endswith('.html'):
                url = QUrl(f"file:///{QDir.fromNativeSeparators(ruta_archivo)}")
                print(f"Cargando archivo: {url}")
                #self.web_view.load(url)
                self.web_view.setUrl(url)
                self.content_area.setCurrentWidget(self.web_view)
                self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.web_view.setZoomFactor(1.0)
            else:
                self.text_browser.setText(f"Archivo no soportado: {ruta_archivo}")
                self.content_area.setCurrentWidget(self.text_browser)

    def agregar_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if carpeta:
            nombre_curso = os.path.basename(carpeta)
            total_archivos = self.contar_archivos(carpeta)
            self.cursos_data[nombre_curso] = {
                "id": nombre_curso,
                "name": nombre_curso,
                "description": f"Descripción del curso {nombre_curso}",
                "totalArchivos": total_archivos,
                "archivosVistos": 0,
                "icon": "SiNextdotjs",
                "archivos": self.obtener_archivos(carpeta),
                "progress": {},
                "ruta": carpeta
            }

            with open("cursos_data.json", "w", encoding="utf-8") as f:
                json.dump(self.cursos_data, f, ensure_ascii=False, indent=2)

            self.actualizar_grid_cursos()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ventana = CursoTracker()
    ventana.show()
    sys.exit(app.exec())