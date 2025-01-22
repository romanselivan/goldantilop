from asyncio.log import logger
import json
import gspread
from google.oauth2.service_account import Credentials
from config import G_SHEET_CRED, CACHE_TTL, RATES_SHEET, REQUESTS_SHEET, USERS_SHEET, RateFields, RequestFields, UserFields
from datetime import datetime

class SheetManager:
    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.sheets = {}
        self.field_indices = {}
        self.cache = {}
        self.cache_ttl = {}
        self.id_fields = {
            USERS_SHEET: UserFields.USER_ID,
            REQUESTS_SHEET: RequestFields.REQUEST_ID,
            RATES_SHEET: RateFields.SOURCE_CURRENCY
        }
        self.client = self._get_client()
        self._init_sheets()

    def _get_client(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        if isinstance(G_SHEET_CRED, Credentials):
            creds = G_SHEET_CRED
        else:
            creds = Credentials.from_service_account_info(json.loads(G_SHEET_CRED), scopes=scope)
        return gspread.authorize(creds)

    def _init_sheets(self):
        spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        for worksheet in spreadsheet.worksheets():
            sheet_name = worksheet.title
            self.sheets[sheet_name] = worksheet
            self._init_field_indices(sheet_name)
        self._cache_data()  # Вызываем _cache_data только один раз после инициализации всех листов

    def _init_field_indices(self, sheet_name):
        headers = self.sheets[sheet_name].row_values(1)
        self.field_indices[sheet_name] = {header: index for index, header in enumerate(headers) if header}
        logger.info(f"Initialized field indices for sheet '{sheet_name}': {self.field_indices[sheet_name]}")
 
    def _cache_data(self):
        for sheet_name, worksheet in self.sheets.items():
            logger.info(f"Caching data for sheet: {sheet_name}")
            all_data = worksheet.get_all_values()[1:]  # Пропускаем заголовки
            if sheet_name == RATES_SHEET:
                self.cache[sheet_name] = {
                    (row[0], row[1]): row for row in all_data if len(row) > 1
                }
            else:
                id_field = self.id_fields.get(sheet_name, 'id')
                id_index = self.field_indices[sheet_name].get(id_field, 0)
                self.cache[sheet_name] = {row[id_index]: row for row in all_data if len(row) > id_index}
            self.cache_ttl[sheet_name] = datetime.now() + CACHE_TTL
            logger.info(f"Cached {len(self.cache[sheet_name])} entries for sheet: {sheet_name}")

    def get_data(self, sheet_name, id_value=None):
        logger.info(f"Getting data from sheet: {sheet_name}, id_value: {id_value}")
        if sheet_name not in self.sheets:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        if datetime.now() > self.cache_ttl.get(sheet_name, datetime.min):
            self._cache_data()

        if sheet_name == RATES_SHEET:
            if id_value is None:
                return [self._format_row_data(sheet_name, row) for row in self.cache[sheet_name].values()]
            elif isinstance(id_value, tuple) and len(id_value) == 2:
                data = self.cache[sheet_name].get(id_value)
                return self._format_row_data(sheet_name, data) if data else None
            else:
                return [self._format_row_data(sheet_name, row) for row in self.cache[sheet_name].values()
                        if row[0] == id_value or row[1] == id_value]
        else:
            if id_value is None:
                return [self._format_row_data(sheet_name, row) for row in self.cache[sheet_name].values()]
            data = self.cache[sheet_name].get(id_value)
            return self._format_row_data(sheet_name, data) if data else None

    def _format_row_data(self, sheet_name, row_data):
        if not row_data:
            return {}
        result = {}
        for field, index in self.field_indices[sheet_name].items():
            if index < len(row_data):
                result[field] = row_data[index]
            else:
                result[field] = None
        return result

    def update_data(self, sheet_name, id_value, updated_data):
        if sheet_name not in self.sheets:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        id_field = self.id_fields.get(sheet_name, 'id')
        id_index = self.field_indices[sheet_name].get(id_field, 0)

        if id_value not in self.cache[sheet_name]:
            row = self.sheets[sheet_name].find(str(id_value), in_column=id_index + 1)
            if row:
                self.cache[sheet_name][id_value] = self.sheets[sheet_name].row_values(row.row)
            else:
                self.cache[sheet_name][id_value] = [''] * len(self.field_indices[sheet_name])

        row_data = self.cache[sheet_name][id_value]
        cells_to_update = []
        for field, value in updated_data.items():
            if field in self.field_indices[sheet_name]:
                index = self.field_indices[sheet_name][field]
                row_data[index] = value
                cells_to_update.append(gspread.Cell(row.row, index + 1, value))

        if cells_to_update:
            self.sheets[sheet_name].update_cells(cells_to_update)
        self.cache[sheet_name][id_value] = row_data

    def add_new_entry(self, sheet_name, data):
        logger.info(f"Adding new entry to sheet: {sheet_name}")
        if sheet_name not in self.sheets:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        id_field = self.id_fields.get(sheet_name, 'id')
        if id_field not in data:
            raise ValueError(f"'{id_field}' must be provided in the data")

        # Получаем актуальные заголовки таблицы
        headers = self.sheets[sheet_name].row_values(1)
        
        # Обновляем field_indices
        self.field_indices[sheet_name] = {header: index for index, header in enumerate(headers) if header}

        new_row = [''] * len(headers)
        for field, value in data.items():
            if field in self.field_indices[sheet_name]:
                if field in ['USER_ID', 'AMOUNT', 'RESULT']:
                    value = str(value).lstrip("'")
                new_row[self.field_indices[sheet_name][field]] = str(value)            
            if field in self.field_indices[sheet_name]:
                new_row[self.field_indices[sheet_name][field]] = str(value)
            else:
                logger.warning(f"Field '{field}' not found in sheet '{sheet_name}'. Skipping.")

        self.sheets[sheet_name].append_row(new_row)
        self.cache[sheet_name][data[id_field]] = new_row
        logger.info(f"New entry added: {data[id_field]}")
        return data[id_field]

    def batch_update(self, sheet_name, id_value, updated_data):
        logger.info(f"Batch updating sheet: {sheet_name}, id: {id_value}")
        if sheet_name not in self.sheets:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        row = self.sheets[sheet_name].find(str(id_value))
        if not row:
            raise ValueError(f"Entry with id {id_value} not found in sheet {sheet_name}")

        cells_to_update = []
        for field, value in updated_data.items():
            if field in self.field_indices[sheet_name]:
                col = self.field_indices[sheet_name][field] + 1
                cells_to_update.append(gspread.Cell(row.row, col, str(value)))

        if cells_to_update:
            self.sheets[sheet_name].update_cells(cells_to_update)
            
        # Обновляем кэш
        if id_value in self.cache[sheet_name]:
            for field, value in updated_data.items():
                if field in self.field_indices[sheet_name]:
                    self.cache[sheet_name][id_value][self.field_indices[sheet_name][field]] = str(value)

        logger.info(f"Updated {len(cells_to_update)} cells for id: {id_value}")


    def batch_add_entries(self, sheet_name, entries):
        worksheet = self.sheets[sheet_name]
        rows_to_add = []
        for entry in entries:
            new_row = [''] * len(self.field_indices[sheet_name])
            for field, value in entry.items():
                if field in self.field_indices[sheet_name]:
                    new_row[self.field_indices[sheet_name][field]] = value
            rows_to_add.append(new_row)
        
        worksheet.append_rows(rows_to_add)
        
        for entry in entries:
            id_field = self.id_fields[sheet_name]
            self.cache[sheet_name][entry[id_field]] = new_row

    def get_multiple_data(self, sheet_name, id_values, fields=None):
        if datetime.now() > self.cache_ttl.get(sheet_name, datetime.min):
            self._cache_data(sheet_name)
        
        results = []
        for id_value in id_values:
            data = self.cache[sheet_name].get(id_value)
            if data:
                results.append(self._format_row_data(sheet_name, data, fields))
        
        return results