import sys
import pandas as pd
from pandasDataModel import PandasModel
import numpy as np
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QCheckBox, QTableView,
    QFileDialog, QLabel, QSplitter, QSizePolicy, QComboBox, QHeaderView
)
from matplotlib.backend_bases import MouseEvent, Event
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from typing import cast


"""
TODO:
-   Add functionality to include swap and commission prices into balance calculation, including a checkbox to be able to
    view the return of the strategy without commission and swap
-   Fix the sidebar view, currently the Index column is cut off
-   Change the display of the graph, currently there are gaps in the graph if there are gaps in the positionIDs
-   Add a checkbox next to each row of the table to be able to exclude single entries (Usecase: errors in the strategy
    or extreme outliers can be accounted for this way)
-   Add the ability to filter for trade direction
-   Add the ability to switch to different graphs with a dropbox, for example plot the volumes, or use the position
    opening time as x-axis
-   Future implementations: Add a statisical overview tab to display some key figures and calculations of the strategy,
    like averages (Position size, return, swap, duration of the position, price difference in %, some important figures 
    like the MT5 Strategy tester has them to be able to compare)
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        """---Application---"""
        # region Application

        """---Main Window---"""
        # region Main Window

        """---main_layout---"""
        # region Init Main Window Layout
        self.setWindowTitle("CSV Table Viewer with Filtering & Visualization")
        self.resize(1000, 600)
        self.showMaximized()
        # Structure
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        # endregion
        """---main_layout---"""

        """---main_layout Contents---"""
        # region main_layout Contents

        """---Sidebar---"""
        # region Add sidebar to main_layout

        # Init
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("background-color: #403e3e; color: white;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        main_layout.addWidget(self.sidebar)

        """Sidebar Contents"""
        # region Sidebar Contents

        """Comment Filter"""
        # region Comment Filter

        # Init Objects
        filter_label = QLabel("Filter:")
        self.filter_input = QLineEdit()
        self.filter_checkbox = QCheckBox("Enable Filter")
        # Style and defaults
        self.filter_input.setStyleSheet("background-color: white; color: black;")
        self.filter_input.setPlaceholderText("Comment filter...")
        # Add to sidebar layout manager
        sidebar_layout.addWidget(filter_label)
        sidebar_layout.addWidget(self.filter_input)
        sidebar_layout.addWidget(self.filter_checkbox)
        # Connections
        self.filter_input.textChanged.connect(self.update_filter)
        self.filter_checkbox.stateChanged.connect(self.update_filter)

        # endregion
        """Comment Filter"""

        """Plot Modes"""
        # region Plot Modes

        # Init Objects
        plot_mode_label = QLabel("Plot Mode:")
        self.plot_mode_combo = QComboBox()
        # Style, Contents and defaults
        self.plot_mode_combo.addItems(["Individual", "Cumulative"])
        self.plot_mode_combo.setStyleSheet("background-color: white; color: black;")
        # Add to sidebar layout manager
        sidebar_layout.addWidget(plot_mode_label)
        sidebar_layout.addWidget(self.plot_mode_combo)
        # Connections
        self.plot_mode_combo.currentIndexChanged.connect(self.update_plot_mode)

        # endregion
        """Plot Modes"""

        """Plot Column Selectors"""
        # region Plot Column Selectors

        # Init Objects
        plot_column_label = QLabel("Plot Columns:")
        self.balance_checkbox = QCheckBox("Balance")
        self.swap_checkbox = QCheckBox("Swap")
        self.commission_checkbox = QCheckBox("Commission")
        # Style, Contents and Defaults
        self.balance_checkbox.setChecked(True)
        self.swap_checkbox.setChecked(True)
        self.commission_checkbox.setChecked(True)
        # Add to sidebar layout manager
        sidebar_layout.addWidget(plot_column_label)
        sidebar_layout.addWidget(self.balance_checkbox)
        sidebar_layout.addWidget(self.swap_checkbox)
        sidebar_layout.addWidget(self.commission_checkbox)
        # Connections
        self.balance_checkbox.stateChanged.connect(self.plot_data)
        self.swap_checkbox.stateChanged.connect(self.plot_data)
        self.commission_checkbox.stateChanged.connect(self.plot_data)

        # endregion
        """Plot Column Selectors"""

        # Stretch at the end
        sidebar_layout.addStretch()

        # endregion
        """Sidebar Contents"""

        # endregion
        """---Sidebar---"""

        """---Main Content---"""
        # region Main Content
        main_content_widget = QWidget()
        main_content_layout = QVBoxLayout(main_content_widget)

        """---Top Bar---"""
        # region Top Bar

        # Add to main_layout
        main_layout.addWidget(main_content_widget)
        top_bar_layout = QHBoxLayout()

        """---Top Bar Contents---"""
        # region Top Bar Content

        # Init Objects
        self.toggle_button = QPushButton("Toggle Sidebar")
        self.load_button = QPushButton("Load CSV")
        # Add to top_bar_layout
        top_bar_layout.addWidget(self.toggle_button)
        top_bar_layout.addWidget(self.load_button)
        top_bar_layout.addStretch()
        # Connections
        self.load_button.clicked.connect(self.load_csv)
        self.toggle_button.clicked.connect(self.toggle_sidebar)

        # endregion
        """---Top Bar Contents---"""

        # Add to main_content_layout
        main_content_layout.addLayout(top_bar_layout)

        # endregion
        """---Top Bar---"""

        """---Vertical Splitter---"""
        # region Vertical Splitter

        # Init Objects
        table_view_canvas_splitter = QSplitter(Qt.Vertical)
        table_view_canvas_splitter.setSizes([1, 40])

        """---Splitter Contents---"""
        # region Splitter Contents

        # Init and defaults
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)

        """---Plotting Area"""
        # region Plotting Area

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.canvas.figure.add_subplot(111)
        self.annot = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="w"),
                                      arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        self.line = Line2D([0], [0])
        # Connections
        self.canvas.mpl_connect("motion_notify_event", self.hover)

        # endregion
        """---Plotting Area"""

        # Add to splitter
        table_view_canvas_splitter.addWidget(self.table_view)
        table_view_canvas_splitter.addWidget(self.canvas)

        # endregion
        """---Splitter Contents---"""

        # Add to main_content_layout
        main_content_layout.addWidget(table_view_canvas_splitter)

        # endregion
        """---Vertical Splitter---"""

        # endregion
        """---Main Content---"""

        # endregion
        """---main_layout Contents---"""

        # endregion
        """---Main Window---"""

        # endregion
        """---Application---"""

        """---Internal Data---"""
        # region Internal data
        self.df = pd.DataFrame()
        self.model = PandasModel()
        self.x_column = "Position ID"
        self.plot_mode = "Individual"
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.table_view.setModel(self.proxy_model)
        # Connections
        self.model.data_updated.connect(self.plot_data)
        # endregion
        """---Internal Data---"""

    def update_plot_mode(self):
        self.plot_mode = self.plot_mode_combo.currentText()
        self.plot_data()

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def load_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV files (*.csv)")
        if file_name:
            try:
                self.df = pd.read_csv(file_name, encoding="utf-16")
                self.model.set_data_frame(self.df)
                header = self.table_view.horizontalHeader()
                last_col_index = self.model.columnCount() - 1
                if last_col_index > 0:
                    header.setSectionResizeMode(last_col_index, QHeaderView.Stretch)
                self.proxy_model.setFilterKeyColumn(len(self.df.columns))
            except Exception as e:
                print(f"Failed to load CSV: {e}")

    def update_filter(self):
        search_text = self.filter_input.text()
        if self.filter_checkbox.isChecked():
            self.proxy_model.setFilterFixedString(search_text)
        else:
            self.proxy_model.setFilterFixedString("")
        self.plot_data()

    def plot_data(self):
        # -- Plot Data --
        # Redraws the plot based on the current data and user selections.
        """Draw a simple matplotlib plot in the bottom area."""
        self.ax.clear()
        self.annot = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="w"),
                                      arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)

        if not self.df.empty:
            # Determine which rows to plot based on filters and checkboxes
            visible_source_indices = {self.proxy_model.mapToSource(self.proxy_model.index(row, 0)).row()
                                      for row in range(self.proxy_model.rowCount())}
            checked_mask = self.model.get_checked_rows_mask()
            indices_to_plot = [i for i, is_checked in enumerate(checked_mask) if
                               is_checked and i in visible_source_indices]
            plotted_df = self.df.iloc[indices_to_plot]

            if not plotted_df.empty and self.x_column:
                try:
                    y_values = pd.Series(np.zeros(len(plotted_df)), index=plotted_df.index)
                    selected_columns = []

                    if self.balance_checkbox.isChecked():
                        y_values += plotted_df['Profit'].fillna(0)
                        selected_columns.append('Balance')
                    if self.swap_checkbox.isChecked():
                        y_values += plotted_df['Swap'].fillna(0)
                        selected_columns.append('Swap')
                    if self.commission_checkbox.isChecked():
                        y_values += plotted_df['Commission'].fillna(0)
                        selected_columns.append('Commission')

                    if not selected_columns:
                        self.line = Line2D([0], [0])
                        self.ax.text(0.5, 0.5, "No data selected", ha="center", va="center",
                                     transform=self.ax.transAxes)
                        self.canvas.draw()
                        return

                    title = f"Plot of {', '.join(selected_columns)} vs {self.x_column}"
                    if self.plot_mode == "Cumulative":
                        y_values = y_values.cumsum()
                        title = f"Cumulative {title}"

                    self.line, = self.ax.plot(plotted_df[self.x_column],
                                              y_values,
                                              marker='o',
                                              markersize=3,
                                              linestyle='-',
                                              color='skyblue')
                    self.ax.set_title(title)
                    self.ax.grid(True)

                    # Offset the x_labels for readability
                    for text in self.ax.get_xticklabels()[1::2]:
                        text.set_y(-0.04)

                except KeyError as e:
                    self.ax.text(0.5, 0.5, f"Column not found: {e}\nPlease check your CSV file.",
                                 ha="center", va="center", transform=self.ax.transAxes)
                except Exception as e:
                    self.ax.text(0.5, 0.5, f"Could not plot Graph, Exception:\n{e}",
                                 ha="center", va="center", transform=self.ax.transAxes)
        else:
            self.ax.text(0.5, 0.5, "No data loaded", ha="center", va="center", transform=self.ax.transAxes)

        self.canvas.draw()

    def update_annot(self, ind):
        # -- Update Annotation --
        # Updates the annotation text and position when hovering over a data point.
        idx = ind["ind"][0]
        x, y = self.line.get_data()
        self.annot.xy = (x[idx], y[idx])

        text = f"{self.x_column}: {x[idx]}\nValue: {y[idx]:.2f}"
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)

    def hover(self, mouse_event: Event):
        # -- Hover Event --
        # Handles mouse hover events to show or hide the data point annotation.
        vis = self.annot.get_visible()
        event = cast(MouseEvent, mouse_event)

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
        distances_sq = np.sum((xy_pixels - (event.x, event.y)) ** 2, axis=1)

        # Find the closest point
        min_dist_ind = np.argmin(distances_sq)

        # Threshold in pixels squared (e.g. 10px radius)
        pixel_threshold_sq = 10 ** 2

        if distances_sq[min_dist_ind] < pixel_threshold_sq:
            self.update_annot({"ind": [min_dist_ind]})
            self.annot.set_visible(True)
            self.canvas.draw_idle()
        else:
            if vis:
                self.annot.set_visible(False)
                self.canvas.draw_idle()

    def showEvent(self, event):
        """Called automatically when the window is shown."""
        # Set focus to the main window to deselect any input widgets
        self.setFocus()
        # Call the parent class's implementation to ensure default behavior
        super().showEvent(event)


def main():
    # -- Main Execution --
    # Initializes and runs the PyQt5 application.
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    # -- Application Entry Point --
    # Ensures that the main function is called only when the script is executed directly.
    main()
