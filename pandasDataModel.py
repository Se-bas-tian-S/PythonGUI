from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal
import pandas as pd
import numpy as np


class PandasModel(QAbstractTableModel):
    """A model to interface a pandas DataFrame with QTableView."""
    data_updated = pyqtSignal()

    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df.copy()
        self._checked_states = [True] * len(self._df)

    def set_data_frame(self, df):
        self.beginResetModel()
        self._df = df.copy()
        self._checked_states = [True] * len(self._df)
        self.endResetModel()
        self.data_updated.emit()

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1] + 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if index.column() == 0:
            if role == Qt.CheckStateRole and index.column() == 0:
                return Qt.Checked if self._checked_states[index.row()] else Qt.Unchecked
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            try:
                raw_value = self._df.iloc[index.row(), index.column() - 1]
                col_name = self._df.columns[index.column() - 1]
            except Exception as e:
                print(f"Data Error in DataModel: {e}")
                return None

            if pd.isna(raw_value):
                return "" if role == Qt.DisplayRole else None  # Display empty string for missing values

            if role == Qt.DisplayRole:
                # Apply specific formatting based on column name
                if col_name in ["Open Price", "Close Price"]:
                    return f"{float(raw_value):.5f}"

                if col_name in ["Commission", "Swap", "Profit", "Volume"]:
                    return f"{float(raw_value):.2f}"

                if isinstance(raw_value, pd.Timestamp):
                    return raw_value.strftime('%Y-%m-%d %H:%M:%S')

                # Fallback for any other column
                return str(raw_value)

                # --- Role for SORTING/EDITING (Raw Data) ---
                # This provides the raw data that the proxy model will use to sort
            if role == Qt.EditRole:
                if pd.isna(raw_value):
                    return None

                # Convert numpy types to standard Python types
                if isinstance(raw_value, np.integer):
                    return int(raw_value)
                if isinstance(raw_value, np.floating):
                    return float(raw_value)

                # For Timestamps, bools, or strings, the raw object is sortable
                return raw_value
        return None

    def setData(self, index, value, role):
        if role == Qt.CheckStateRole and index.column() == 0:
            self._checked_states[index.row()] = (value == Qt.Checked)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            self.data_updated.emit()
            return True
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return ""  # Header for checkbox column
                return self._df.columns[section - 1]
            if orientation == Qt.Vertical:
                return str(self._df.index[section])
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == 0:
            return super().flags(index) | Qt.ItemIsUserCheckable
        return super().flags(index)

    def get_checked_rows_mask(self):
        return self._checked_states