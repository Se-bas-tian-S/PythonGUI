import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QCheckBox, QTableView, QFileDialog, QLabel,
    QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from pandasDataModel import PandasModel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Table Viewer with Filtering & Visualization")
        self.resize(1000, 600)

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
        splitter.addWidget(self.canvas)

        layout.addWidget(splitter)

        # Internal data
        self.df = pd.DataFrame()
        self.model = PandasModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # search all columns

        self.table_view.setModel(self.proxy_model)

        # Connections
        self.load_button.clicked.connect(self.load_csv)
        self.filter_input.textChanged.connect(self.update_filter)
        self.filter_checkbox.stateChanged.connect(self.update_filter)

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

    def plot_data(self, column=None):
        """Draw a simple matplotlib plot in the bottom area."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not self.df.empty:
            if column is None:
                # Default: plot histogram of first numeric column
                numeric_cols = self.df.select_dtypes(include="number").columns
                if len(numeric_cols) > 0:
                    column = numeric_cols[0]

            if column:
                try:
                    self.df[column].dropna().hist(ax=ax, bins=20, color="skyblue", edgecolor="black")
                    ax.set_title(f"Histogram of {column}")
                except Exception as e:
                    ax.text(0.5, 0.5, f"Could not plot column '{column}'\n{e}",
                            ha="center", va="center", transform=ax.transAxes)

        else:
            ax.text(0.5, 0.5, "No data loaded", ha="center", va="center", transform=ax.transAxes)

        self.canvas.draw()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
