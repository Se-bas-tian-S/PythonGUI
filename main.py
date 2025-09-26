import sys
import pandas as pd
import numpy as np
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
        self.plotted_df = pd.DataFrame()
        self.model = PandasModel()
        self.x_column = "Position ID"
        self.y_column = "Profit"
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
                self.df = pd.read_csv(file_name, encoding="utf-16")
                self.plotted_df = self.df
                self.model.set_data_frame(self.df)
                self.plot_data()
                self.proxy_model.setFilterKeyColumn(len(self.df.columns) - 1)
            except Exception as e:
                print(f"Failed to load CSV: {e}")

    def update_filter(self):
        search_text = self.filter_input.text()
        if self.filter_checkbox.isChecked():
            self.proxy_model.setFilterFixedString(search_text)
            source_indices = [self.proxy_model.mapToSource(self.proxy_model.index(row, 0)).row()
                              for row in range(self.proxy_model.rowCount())]
            self.plotted_df = self.df.iloc[source_indices]
        else:
            self.proxy_model.setFilterFixedString("")
            self.plotted_df = self.df

        self.plot_data()

    def plot_data(self):
        """Draw a simple matplotlib plot in the bottom area."""
        self.ax.clear()
        self.annot = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="w"),
                                      arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)


        if not self.plotted_df.empty:
            if self.x_column and self.y_column:
                try:
                    self.line, = self.ax.plot(self.plotted_df[self.x_column], self.plotted_df[self.y_column], marker='o', linestyle='-', color='skyblue')
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
        # Get the specific data point's coordinates
        x_val = self.df[self.x_column].iloc[ind["ind"][0]]
        y_val = self.df[self.y_column].iloc[ind["ind"][0]]
        text = f"{self.x_column}: {x_val}\n{self.y_column}: {y_val}"
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)

    def hover(self, event: MouseEvent):
        vis = self.annot.get_visible()

        # If mouse is not in our axes, hide annotation and return
        if not event.inaxes:
            if vis:
                self.annot.set_visible(False)
                self.canvas.draw_idle()
            return

        # Get data points from the line object
        x_data, y_data = self.line.get_data()

        # If there's no data, do nothing
        if len(x_data) == 0:
            return

        # Transform data coords to display coords
        xy_pixels = self.ax.transData.transform(np.c_[x_data, y_data])

        # Calculate squared distance from mouse to all points in pixel space
        distances_sq = np.sum((xy_pixels - (event.x, event.y))**2, axis=1)

        # Find the closest point
        min_dist_ind = np.argmin(distances_sq)

        # Threshold in pixels squared (e.g. 10px radius)
        pixel_threshold_sq = 10**2

        if distances_sq[min_dist_ind] < pixel_threshold_sq:
            self.update_annot({"ind": [min_dist_ind]})
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
