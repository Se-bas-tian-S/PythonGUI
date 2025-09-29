from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal
import pandas as pd


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
        if role == Qt.CheckStateRole and index.column() == 0:
            return Qt.Checked if self._checked_states[index.row()] else Qt.Unchecked
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return None  # Checkbox column
            return str(self._df.iloc[index.row(), index.column() - 1])
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