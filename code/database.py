import gspread
import gspread_formatting as gf
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import sys
import operator
from cards import allIn, noneIn

# Define the scope of access for the Google Sheets API
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Path to the credentials file for Google Sheets API
CREDENTIALS_PATH = 'credentials.json'

# Load credentials from the specified JSON file
CREDS = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, SCOPE)

# Temporary path for saving and loading database CSV files
TEMP_PATH = 'code/database.csv'

# Range in the Google Sheet representing the header row
HEADER_RANGE = 'A1:J1'

# Supported comparison operators for database queries
OPERATORS = {
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    '==': operator.eq,
    '!=': operator.ne
}

class CardDatabase:
    """
    Handles operations on the card database, including querying, updating, and synchronizing
    with a Google Sheet. Uses pandas for internal data management.
    """
    def __init__(self, sheet_name):
        """
        Initializes the CardDatabase object by connecting to a Google Sheet
        and loading its data into a pandas DataFrame.

        :param sheet_name: Name of the Google Sheet to connect to.
        """
        try:
            self.client = gspread.authorize(CREDS)
            self.spreadsheet = self.client.open(sheet_name)
            self.sheet = self.spreadsheet.sheet1

            # Load data from the sheet into a pandas DataFrame
            data = self.sheet.get_all_values()
            self.columns = data[0]  # Extract column headers
            rows = data[1:]  # Extract data rows
            self._df = pd.DataFrame(rows, columns=self.columns, dtype=object)
        except Exception as e:
            print("Couldn't get online sheet, loading internal csv...")
            self.load()

    def update(self):
        """
        Updates the Google Sheet with the current DataFrame contents.
        Formats the sheet for better readability.
        """
        # Sort the DataFrame and fill empty cells
        self._df.sort_values(by=self.columns[0], ascending=True, inplace=True)
        self._df = self._df.fillna('')
        self.save()  # Save the current state to a CSV file

        try: 
            # Prepare the data for updating the sheet
            values = [self._df.columns.tolist()] + self._df.values.tolist()
            self.sheet.clear()  # Clear the existing data in the sheet
            self.sheet.update(range_name='A1', values=values)  # Update with new data

            # Format the entire sheet with light gray borders
            light_gray = gf.Color(0.8, 0.8, 0.8)
            gf.format_cell_range(self.sheet, 'A:Z', gf.CellFormat(
                borders=gf.Borders(
                    top=gf.Border(style='SOLID', color=light_gray),
                    bottom=gf.Border(style='SOLID', color=light_gray),
                    left=gf.Border(style='SOLID', color=light_gray),
                    right=gf.Border(style='SOLID', color=light_gray)
                )
            ))

            # Format the header row with thick borders
            gf.format_cell_range(self.sheet, HEADER_RANGE, gf.CellFormat(
                borders=gf.Borders(
                    top=gf.Border(style='SOLID_THICK'),
                    bottom=gf.Border(style='SOLID_THICK'),
                    left=gf.Border(style='SOLID_THICK'),
                    right=gf.Border(style='SOLID_THICK')
                )
            ))

            # Format individual data ranges
            col_range = f'A2:I{len(self)+1}'
            gf.format_cell_range(self.sheet, col_range, gf.CellFormat(
                borders=gf.Borders(
                    right=gf.Border(style='SOLID_THICK')
                )
            ))

            # Format the bottom border of the last row
            bottom_range = f'A{len(self)+1}:I{len(self)+1}'
            gf.format_cell_range(self.sheet, bottom_range, gf.CellFormat(
                borders=gf.Borders(
                    bottom=gf.Border(style='SOLID_THICK')
                )
            ))

            print("Database Updated.")
        except Exception as e:
            print("Can't access online database but saved internally")

    def getAll(self, key: str, values: str, op='=='):
        """
        Retrieves rows from the DataFrame that satisfy a condition on a specified column.

        :param key: Column name to apply the condition to.
        :param values: Values to compare against, separated by spaces.
        :param op: Comparison operator, e.g., '==', '!='. Defaults to '=='.
        :return: Filtered DataFrame containing matching rows.
        """
        values = values.strip().split()

        if op == '==':
            func = allIn
        elif op == '!=':
            func = noneIn
        else:
            print(f"<<<ERROR>>> Database.py -> getAll: {op} is an invalid operator")
            sys.exit()

        func2apply = lambda row: func(row[key], *values)
        mask = self._df.apply(func2apply, axis=1)
        return self._df[mask]

    def sort(self, by, ascending=True):
        """
        Sorts the DataFrame by a specified column.

        :param by: Column name to sort by.
        :param ascending: Whether to sort in ascending order. Defaults to True.
        """
        try:
            self._df = self._df.sort_values(by=by, ascending=ascending)
        except Exception as e:
            print(f"\n<<<ERROR>>> database.py -> sort: Couldn't sort by {by}")
            sys.exit()

    def save(self, path=TEMP_PATH):
        """
        Saves the DataFrame to a CSV file at the specified path.

        :param path: Path to save the CSV file.
        """
        self._df.to_csv(path, index=False)
        print("Saved database to", path)

    def load(self, path=TEMP_PATH):
        """
        Loads the DataFrame from a CSV file at the specified path.

        :param path: Path to the CSV file.
        """
        self._df = pd.read_csv(path)
        self.columns = self._df.columns
        print("Loaded database from", path)

    def __len__(self):
        """
        Returns the number of rows in the DataFrame.
        """
        return len(self._df)

    def __getitem__(self, idx):
        """
        Retrieves an item from the DataFrame based on the given index.

        :param idx: Column name, row index, or primary key.
        """

        if idx in self.columns:  # Access column by name
            return self._df[idx]
        elif isinstance(idx, tuple): # Access row by condition
            try:
                idx, op, thres = idx
                if isinstance(thres, str):
                    return self.getAll(idx, thres, op)
                return self._df[OPERATORS[op](self._df[idx].astype(type(thres)), thres)]
            except Exception as e:
                print(f"\nCan't get database by cond because '{idx} {op} {thres}'")
                raise
        elif isinstance(idx, (int, slice)):  # Access row by index or rows by slice
            try:
                return self._df.iloc[idx]
            except Exception as e:
                print(f"\n<<<ERROR>>> database: Only has {len(self)} items but requested item {idx+1}\n")
                sys.exit()
        else:  # Access row by card title
            try:
                if idx not in self._df[self.columns[0]].to_list():
                    raise
                return self._df.loc[self._df[self.columns[0]] == idx].iloc[0]
            except Exception as e:
                print(f"\n<<<ERROR>>> database: Could not find card '{idx}' in the database\n")

    def __setitem__(self, idx, value):
        """
        Updates or inserts a row in the DataFrame based on the given index.

        :param idx: Row index or primary key.
        :param value: Row data to be inserted or updated.
        """
        if isinstance(value, dict):
            new_val = pd.Series(index=list(self.columns), dtype=object)
            for key, val in value.items():
                if key in new_val.index:
                    new_val[key] = val
            value = new_val

        if isinstance(idx, int):  # Update row by index
            self._df.iloc[idx] = value
        else:  # Update or insert row by primary key
            if idx in self._df[self.columns[0]].to_list():
                idx = self._df.index[self._df[self.columns[0]] == idx][0]
                self._df.iloc[idx] = value
            elif value[self.columns[0]] in self._df[self.columns[0]].to_list():
                idx = self._df.index[self._df[self.columns[0]] == value[self.columns[0]]][0]
                self._df.iloc[idx] = value
            else:  # Add a new row
                self._df.loc[len(self)] = value
                self._df = self._df.fillna('')

    def __repr__(self):
        """
        Returns a string representation of the DataFrame.
        """
        return str(self._df)
    
    def __iter__(self):
        """
        Allows iteration over the rows of the DataFrame.
        """
        return self._df.iterrows()

if __name__ == '__main__':
    # Example usage of the CardDatabase class
    test = CardDatabase("mtgscp")
    new_row = pd.Series(index=test.columns, dtype=object)
    new_row['Card'] = 'TestCard'  # Example card data
    test['TestCard'] = new_row  # Add the new row by primary key
    test[10] = new_row  # Add the new row by index
    print(test)
    test.update()
