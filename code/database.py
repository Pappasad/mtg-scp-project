import gspread
import gspread_formatting as gf
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import sys

# Define the scope of access for the Google Sheets API
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Path to the credentials file for Google Sheets API
CREDENTIALS_PATH = 'credentials.json'

# Load credentials from the specified JSON file
CREDS = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, SCOPE)

# Temporary path for saving and loading database CSV files
TEMP_PATH = 'code/database.csv'

# Range in the Google Sheet representing the header row
HEADER_RANGE = 'A1:I1'

class CardDatabase:
    def __init__(self, sheet_name):
        """
        Initializes the CardDatabase object by connecting to a Google Sheet
        and loading its data into a pandas DataFrame.

        :param sheet_name: Name of the Google Sheet to connect to.
        """
        # Authorize and access the Google Sheet
        self.client = gspread.authorize(CREDS)
        self.spreadsheet = self.client.open(sheet_name)
        self.sheet = self.spreadsheet.sheet1

        # Load data from the sheet into a pandas DataFrame
        data = self.sheet.get_all_values()
        self.columns = data[0]  # Extract column headers
        rows = data[1:]  # Extract data rows
        self._df = pd.DataFrame(rows, columns=self.columns, dtype=object)

    def update(self):
        """
        Updates the Google Sheet with the current DataFrame contents.
        Formats the sheet for better readability.
        """
        self.save()  # Save the current state to a CSV file
        
        # Sort the DataFrame and fill empty cells
        self._df.sort_values(by=self.columns[0], ascending=True, inplace=True)
        self._df = self._df.fillna('')
        
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

    def save(self, path=TEMP_PATH):
        """
        Saves the DataFrame to a CSV file at the specified path.

        :param path: Path to save the CSV file.
        """
        self._df.to_csv(path)
        print("Saved database to", path)

    def load(self, path=TEMP_PATH):
        """
        Loads the DataFrame from a CSV file at the specified path.

        :param path: Path to the CSV file.
        """
        self._df = pd.read_csv(path)
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
        elif isinstance(idx, (int, slice)):  # Access row by index
            try:
                return self._df.iloc[idx]
            except:
                print(f"\n<<<ERROR>>> database: Only has {len(self)} items but requested item {idx+1}\n")
                sys.exit()
        else:  # Access row by primary key
            try:
                if idx not in self._df[self.columns[0]].to_list():
                    raise
                return self._df.loc[self._df[self.columns[0]] == idx].iloc[0]
            except:
                print(f"\n<<<ERROR>>> database: Could not find card '{idx}' in the database\n")
                sys.exit()

    def __setitem__(self, idx, value):
        """
        Updates or inserts a row in the DataFrame based on the given index.

        :param idx: Row index or primary key.
        :param value: Row data to be inserted or updated.
        """
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

if __name__ == '__main__':
    # Example usage of the CardDatabase class
    test = CardDatabase("mtgscp")
    new_row = pd.Series(index=test.columns, dtype=object)
    new_row['Card'] = 'cumguzzler420'  # Example card data
    test['cumguzzler420'] = new_row  # Add the new row by primary key
    test[10] = new_row  # Add the new row by index
    print(test)
    test.update()
