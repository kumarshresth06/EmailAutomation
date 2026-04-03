import os
import pandas as pd

class DataHandler:
    def __init__(self, filepath, output_path=None, logger=None):
        self.filepath = filepath
        self.output_path = output_path or filepath
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
        if 'Date_Sent' not in self.df.columns:
            self.df['Date_Sent'] = ""
            
        self.email_col = 'Email' if 'Email' in self.df.columns else 'email' if 'email' in self.df.columns else None

    def get_missing_placeholders(self, placeholders):
        if self.df is None:
            return list(placeholders)
        return [p for p in placeholders if p not in self.df.columns]
        
    def has_email_column(self):
        return self.email_col is not None

    def has_fallback_columns(self):
        if self.df is None: return False
        required = ['First Name', 'Last Name', 'Company']
        for r in required:
            if r not in self.df.columns:
                return False
        return True

    def save_state(self):
        if self.ext == '.csv':
            self.df.to_csv(self.output_path, index=False)
        else:
            self.df.to_excel(self.output_path, index=False)

    def mark_sent(self, index, timestamp):
        self.df.at[index, 'Status'] = 'Sent'
        self.df.at[index, 'Date_Sent'] = timestamp
        self.save_state()


    def get_sample_row(self, placeholders):
        if self.df is None:
            return None
        
        for index, row in self.df.iterrows():
            has_valid_dest = False
            
            # Check direct email first
            if self.email_col and not pd.isna(row[self.email_col]) and str(row[self.email_col]).strip() != '':
                has_valid_dest = True
            # Fallback check
            elif self.has_fallback_columns():
                fn = str(row['First Name']).strip() if not pd.isna(row['First Name']) else ''
                ln = str(row['Last Name']).strip() if not pd.isna(row['Last Name']) else ''
                co = str(row['Company']).strip() if not pd.isna(row['Company']) else ''
                if fn and ln and co:
                    has_valid_dest = True
                    
            if not has_valid_dest:
                continue
                
            has_blank = False
            for p in placeholders:
                if pd.isna(row[p]) or str(row[p]).strip() == '':
                    has_blank = True
                    break
            if not has_blank:
                return row
        return None
