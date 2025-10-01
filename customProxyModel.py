from PyQt5.QtCore import QSortFilterProxyModel, Qt


class CustomProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._direction_filter = ""
        self._comment_filter = ""
        self._comment_filter_enabled = False

    def set_direction_filter(self, direction):
        self._direction_filter = direction
        self.invalidateFilter()

    def set_comment_filter(self, text, enabled):
        self._comment_filter = text
        self._comment_filter_enabled = enabled
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        # Direction filter logic
        direction_accepted = True
        if self._direction_filter and self._direction_filter != "Both":
            try:
                # get_loc gives the integer index of the 'direction' column in the dataframe, + 1 for checkbox col
                direction_col_df_index = self.sourceModel()._df.columns.get_loc("Direction") + 1
                source_index = self.sourceModel().index(source_row, direction_col_df_index, source_parent)
                direction_data = self.sourceModel().data(source_index, Qt.DisplayRole)
                if direction_data is None or self._direction_filter.lower() != direction_data.lower():
                    direction_accepted = False
            except KeyError:
                # 'direction' column not found, so we can't filter.
                # We assume it doesn't match if the column is missing.
                direction_accepted = False

        # Comment filter logic
        comment_accepted = True
        if self._comment_filter_enabled and self._comment_filter:
            comment_accepted = False
            for i in range(self.sourceModel().columnCount()):
                index = self.sourceModel().index(source_row, i, source_parent)
                if index.isValid():
                    cell_data = str(self.sourceModel().data(index, Qt.DisplayRole))
                    if self._comment_filter.lower() in cell_data.lower():
                        comment_accepted = True
                        break

        return direction_accepted and comment_accepted
