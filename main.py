from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QCalendarWidget, QApplication, QMainWindow
from PyQt5.QtCore import QDate
import sys


class WeekCalendar(QCalendarWidget):
    def __init__(self, *args):

        QCalendarWidget.__init__(self, *args)
        self.color = QColor(self.palette().color(QPalette.Highlight))
        self.color.setAlpha(64)
        self.selectionChanged.connect(self.updateCells)

    def paintCell(self, painter, rect, date):

        QCalendarWidget.paintCell(self, painter, rect, date)

        first_day = self.firstDayOfWeek()
        last_day = first_day + 6
        current_date = self.selectedDate()
        current_day = current_date.dayOfWeek()

        if first_day <= current_day:
            first_date = current_date.addDays(first_day - current_day)
        else:
            first_date = current_date.addDays(first_day - 7 - current_day)
        last_date = first_date.addDays(6)

        if first_date <= date <= last_date:
            painter.fillRect(rect, self.color)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendar Example")
        self.calendar = WeekCalendar(self)
        self.setCentralWidget(self.calendar)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
