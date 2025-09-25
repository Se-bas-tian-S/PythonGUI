import sys
from asyncio import Event
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QCheckBox, QTableView, QFileDialog, QLabel,
    QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from matplotlib.backend_bases import MouseEvent
from matplotlib.lines import Line2D

from pandasDataModel import PandasModel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure#
from typing import cast


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Table Viewer with Filtering & Visualization")
        self.resize(1000, 600)
        self.showMaximized()

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Toolbar: Load Button, Filter Input, Checkbox
        toolbar_layout = QHBoxLayout()
        self.load_button = QPushButton("Load CSV")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter...")
        self.filter_checkbox = QCheckBox("Enable Filter")

        toolbar_layout.addWidget(self.load_button)
        toolbar_layout.addWidget(QLabel("Filter:"))
        toolbar_layout.addWidget(self.filter_input)
        toolbar_layout.addWidget(self.filter_checkbox)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Splitter: Table (top) and Visualization Area (bottom)
        splitter = QSplitter(Qt.Vertical)

        # Table
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        splitter.addWidget(self.table_view)

        # Visualization area (matplotlib canvas)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.canvas.figure.add_subplot(111)
        self.annot = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                 bbox=dict(boxstyle="round", fc="w"),
                                 arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        self.line = Line2D([0], [0])
        splitter.addWidget(self.canvas)

        layout.addWidget(splitter)

        # Internal data
        self.df = pd.DataFrame()
        self.model = PandasModel()
        self.x_column = "Date"
        self.y_column = "Balance"
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # search all columns

        self.table_view.setModel(self.proxy_model)

        # Connections
        self.filter_input.textChanged.connect(self.update_filter)
        self.filter_checkbox.stateChanged.connect(self.update_filter)
        self.load_button.clicked.connect(self.load_csv)
        self.canvas.mpl_connect("motion_notify_event", self.hover)

    def load_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV files (*.csv)")
        if file_name:
            try:
                self.df = pd.read_csv(file_name)
                self.model.set_data_frame(self.df)
                self.plot_data()
            except Exception as e:
                print(f"Failed to load CSV: {e}")

    def update_filter(self):
        if self.filter_checkbox.isChecked():
            search_text = self.filter_input.text()
            self.proxy_model.setFilterFixedString(search_text)
        else:
            self.proxy_model.setFilterFixedString("")

    def plot_data(self):
        """Draw a simple matplotlib plot in the bottom area."""
        self.canvas.figure.clf()


        if not self.df.empty:
            if self.x_column and self.y_column:
                try:
                    self.ax.plot(self.df[self.x_column], self.df[self.y_column], marker='o', linestyle='-', color='skyblue')
                    self.ax.set_title(f"Plot {self.y_column} vs {self.x_column}")
                    self.ax.grid(True)

                    # Offset the x_labels for readability
                    for text in self.ax.get_xticklabels()[1::2]:
                        text.set_y(-0.04)


                except Exception as e:
                    self.ax.text(0.5, 0.5, f"Could not plot Graph, Exception:\n{e}",
                            ha="center", va="center", transform=self.ax.transAxes)

        else:
            self.ax.text(0.5, 0.5, "No data loaded", ha="center", va="center", transform=self.ax.transAxes)

        self.canvas.draw()

    def update_annot(self, ind):
        x, y = self.line.get_data()
        self.annot.xy = (x[ind["ind"][0]], y[ind["ind"][0]])
        text = "{}, {}".format(self.df[self.x_column],
                               self.df[self.x_column])
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)

    def hover(self, mouse_event: Event):
        event = cast(MouseEvent, mouse_event)
        vis = self.annot.get_visible()
        if event.inaxes == self.ax:
            cont, ind = self.line.contains(event)
            if cont:
                self.update_annot(ind)
                self.annot.set_visible(True)
                self.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
