import os
import pandas as pd

class DataHandler:
    def __init__(self, filepath, logger=None):
        self.filepath = filepath
        self.ext = os.path.splitext(filepath)[1].lower()
        self.logger = logger
        self.df = None
        self.email_col = None

    def log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def load_data(self):
        if self.ext == '.csv':
            self.df = pd.read_csv(self.filepath)
        else:
            self.df = pd.read_excel(self.filepath)

        if 'Status' not in self.df.columns:
            self.df['Status'] = ""
            self.log("Created 'Status' column.")
        if 'Date_Sent' not in self.df.columns:
            self.df['Date_Sent'] = ""
            self.log("Created 'Date_Sent' column.")
            
        self.email_col = 'Email' if 'Email' in self.df.columns else 'email' if 'email' in self.df.columns else None

    def get_missing_placeholders(self, placeholders):
        if self.df is None:
            return list(placeholders)
        return [p for p in placeholders if p not in self.df.columns]
        
    def has_email_column(self):
        return self.email_col is not None

    def save_state(self):
        if self.ext == '.csv':
            self.df.to_csv(self.filepath, index=False)
        else:
            self.df.to_excel(self.filepath, index=False)

    def mark_sent(self, index, timestamp):
        self.df.at[index, 'Status'] = 'Sent'
        self.df.at[index, 'Date_Sent'] = timestamp
        self.save_state()

    def get_sample_row(self, placeholders):
        if self.df is None or not self.email_col:
            return None
        
        for index, row in self.df.iterrows():
            if pd.isna(row[self.email_col]) or not str(row[self.email_col]).strip():
                continue
                
            has_blank = False
            for p in placeholders:
                if pd.isna(row[p]) or str(row[p]).strip() == '':
                    has_blank = True
                    break
            if not has_blank:
                return row
        return None
