from PyQt5.QtGui import QStandardItemModel, QStandardItem
import pandas as pd


class PandasModel(QStandardItemModel):
    """
    A simple model to populate QTableView with a pandas DataFrame
    """
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self.set_data_frame(df)

    def set_data_frame(self, df):
        self.clear()
        if df.empty:
            return
        # Set headers
        self.setColumnCount(len(df.columns))
        self.setHorizontalHeaderLabels(df.columns.tolist())
        # Fill data
        for row in df.itertuples(index=False):
            items = [QStandardItem(str(field)) for field in row]
            self.appendRow(items)
