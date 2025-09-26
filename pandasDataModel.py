from PyQt5.QtCore import QAbstractTableModel, Qt
import pandas as pd


class PandasModel(QAbstractTableModel):
    """A model to interface a pandas DataFrame with QTableView."""
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df.copy()

    def set_data_frame(self, df):
        self.beginResetModel()
        self._df = df.copy()
        self.endResetModel()

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._df.columns[section]
        return None