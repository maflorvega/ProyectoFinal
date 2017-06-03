import xlsxwriter
import datetime
import StringIO

# Default formatting options object
_DEFAULT_FORMATTING = {
    'title': {
        'bold': True,
        'font_size': 20,
        'align': 'center',
        'valign': 'vcenter',
        'bottom': 5,
        'font_name': 'Times New Roman'
    },
    'description': {
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Times New Roman'
    },
    'bold': {
        'bold': True,
        'font_name': 'Times New Roman'
    },
    'wrap': {
        'text_wrap': True,
        'align': 'right',
        'valign': 'top',
        'font_size': 9,
        'font_name': 'Times New Roman'
    },
    'center': {
        'align': 'center',
        'font_name': 'Times New Roman'
    },
    'left': {
        'align': 'left',
        'font_name': 'Times New Roman'
    },
    'right': {
        'align': 'right',
        'font_name': 'Times New Roman'
    },
    'font': {
        'font_name': 'Times New Roman'
    },
    'day_left': {
        'align': 'left',
        'num_format': 'mmmm d yyyy',
        'font_name': 'Times New Roman'
    },
    'day_right': {
        'align': 'right',
        'num_format': 'mmmm d yyyy',
        'font_name': 'Times New Roman'
    },
    'format1': {
        'bold': True,
        'font_color': 'white',
        'bg_color': 'black',
        'border': True
    },
    'format2': {
        'border': True
    },
    'reportTitle': {
        'text_wrap': True,
        'font_size': 18,
        'align': 'left',
        'valign': 'vjustify',
        'font_name': 'Times New Roman'
    },
    'subtitle': {
        'text_wrap': True,
        'font_size': 12,
        'align': 'left',
        'valign': 'vjustify',
        'font_name': 'Times New Roman'
    }
}


class ExcelReport:
    """
    Excel Report wrapper
    """

    def __init__(self, formatting=_DEFAULT_FORMATTING):
        """
        Initializes a report.
        :param formatting: Optional argument to setup different configuration
          settings.
        """
        self._current_sheet = 1
        self._buffer = StringIO.StringIO()
        self._workbook = xlsxwriter.Workbook(self._buffer,  {'in_memory': True})
        self._styles = self.setup_styles(formatting)

    def setup_styles(self, formatting):
        """
        Iterates through the received configuration structure and build the
        corresponding required objects.

        :param workbook: Excel workbook to work on
        :param formatting: Structure containing all the styles used throughout
          the generated report
        """
        return {key: self._workbook.add_format(formatting[key])
                for key in formatting.keys()}

    def add_cover(self, filters, reports):
        """
        Create a cover for the workbook with Mansion Global boilerplate stuff
        and some information regarding the sheets containing the actual reports.

        :param filters: Dictionary containing filters specified as
          "name": "value". For example:
              {
                'startdate': '2016-05-03',
                'enddate': '2016-05-25'
              }
        :param reports: List of included report names
        """
        # Create an initial worksheet
        worksheet = self._workbook.add_worksheet('Details')

        # Set columns width
        worksheet.set_column(0, 0, 45)
        worksheet.set_column(1, 1, 3)
        worksheet.set_column(2, 3, 20)
        worksheet.set_column(4, 4, 25)

        # Row 0
        worksheet.set_row(0, 35)
        worksheet.write(0, 0, 'MANSION GLOBAL', self._styles['title'])

        worksheet.merge_range(
            0,
            2,
            0,
            4,
            ('For any queries about this report please contact your Mansion '
             'Global sales representative'),
            self._styles['wrap']
        )

        # Row 1
        worksheet.set_row(1, 25)
        worksheet.write(
            1,
            0,
            'ONLY THE EXCEPTIONAL',
            self._styles['description']
        )

        # Row 3
        worksheet.write(
            3,
            0,
            '1211 Ave of the Americas New York, NY 10036',
            self._styles['font']
        )

        worksheet.write(3, 2, 'Report Generated on:', self._styles['right'])

        d = datetime.datetime.now()
        worksheet.write(3, 3, d, self._styles['day_right'])

        # Row 5
        worksheet.write(6, 0, 'Reports', self._styles['bold'])
        worksheet.write(6, 2, 'Filters Applied', self._styles['bold'])

        # Reports Exported
        for offset, report in enumerate(reports):
            worksheet.write(7 + offset, 0, report, self._styles['font'])

        # Filters Applied
        for offset, f in enumerate(filters):
            worksheet.write(7 + offset, 2, f, self._styles['font'])
            worksheet.write(7 + offset, 3, filters[f], self._styles['font'])

    def __add_widget(self, worksheet, name, columns, rows,
                     description=None, autofilter=None, initial_row=0):
        """
        Adds a new sheet to the report being created.

        :param name: Sheet name
        :param columns: Array oc column names
        :param rows: Array of rows (represented as dictionary objects)
        :param description: Sheet description.
        :param autofilter: ?
        """
        TITLE_FIRST_COL = 0
        TITLE_LAST_COL = 2

        DESC_FIRST_COL = 0
        DESC_LAST_COL = 2

        AF_COL = 0

        # Keep track of row count.
        row_count = 0
        # Add title and description
        if name:
            worksheet.merge_range(
                initial_row,
                TITLE_FIRST_COL,
                initial_row,
                TITLE_LAST_COL,
                name,
                self._styles['title']
            )
            row_count += 1
        if description:
            worksheet.merge_range(
                initial_row + row_count,
                DESC_FIRST_COL,
                initial_row + row_count,
                DESC_LAST_COL,
                description,
                self._styles['subtitle']
            )
            row_count += 1

        row_count += 1  # Add a blank line between description and widget

        # Adds autofilter on all columns if autofilter argument is true
        if autofilter:
            worksheet.autofilter(
                initial_row + row_count,
                AF_COL,
                initial_row + len(rows) + 1,
                len(columns) - 1
            )

        # Defines the header
        for cindex, column in enumerate(columns):
            worksheet.write(
                initial_row + row_count,
                cindex,
                column,
                self._styles['format1']
            )
        row_count += 1

        # Writes each row for each column
        for row_index, row in enumerate(rows, initial_row + row_count):
            for col_index, column in enumerate(columns):
                worksheet.write(
                    row_index,
                    col_index,
                    row[column],
                    self._styles['format2']
                )
                worksheet.set_column(row_index, col_index, 25)

        return row_count + len(rows) + 3  # name, description, header, rows

    def add_sheet(self, sheet_name, widgets):
        """
        Creates a new sheet containing the widgets received.

        :param widgets: List of dictionaries containing the following structure:
            [
                {
                    name: widget_name,
                    columns: column names (in order),
                    rows: list of dictionaries:
                        [{c1_name: c1_value}, {c2_name: c2_value}],
                    description: string
                    autofilter: ?
                },
                ...
            ]
        """
        # If all widgets are empty, don't create a sheet
        total_rows = sum([len(w['rows']) for w in widgets])
        if total_rows == 0: return

        MAX_LENGTH_SHEET_TITLE = 31
        worksheet = self._workbook.add_worksheet(
            ("%s. %s" % (self._current_sheet, sheet_name))[:MAX_LENGTH_SHEET_TITLE]
        )

        self._current_sheet += 1

        # We need to provide a starting row for the widget to be inserted, since
        # we might have more than one widget per page now.
        row_count = 0
        for widget in widgets:
            row_count += self.__add_widget(
                worksheet,
                widget['name'],
                widget['columns'],
                widget['rows'],
                widget['description'],
                widget['autofilter'],
                row_count
            )

    def finish(self):
        """
        Closes the workbook and returns a StringIO buffer object with the
        contents.
        """
        self._workbook.close()
        self._buffer.seek(0)
        return self._buffer
