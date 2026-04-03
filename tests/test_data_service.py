import pytest
import os
import pandas as pd
from data_service import DataHandler

@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame({
        'Email': ['test1@example.com', 'test2@example.com', 'test3@example.com'],
        'Name': ['Alice', 'Bob', 'Charlie'],
        'EmptyCol': ['Val', '', 'Val2']
    })
    filepath = tmp_path / "test_data.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)

def test_load_data(sample_csv):
    handler = DataHandler(sample_csv)
    handler.load_data()
    
    assert 'Status' in handler.df.columns
    assert 'Date_Sent' in handler.df.columns
    assert handler.email_col == 'Email'

def test_get_missing_placeholders(sample_csv):
    handler = DataHandler(sample_csv)
    handler.load_data()
    
    missing = handler.get_missing_placeholders(['Name', 'NonExistent'])
    assert missing == ['NonExistent']

def test_get_sample_row(sample_csv):
    handler = DataHandler(sample_csv)
    handler.load_data()
    
    row = handler.get_sample_row(['Name', 'EmptyCol'])
    assert row is not None
    assert row['Name'] == 'Alice'

def test_get_sample_row_with_blanks(sample_csv):
    handler = DataHandler(sample_csv)
    handler.load_data()
    
    handler.df.at[0, 'Name'] = ''
    
    row = handler.get_sample_row(['Name', 'EmptyCol'])
    assert row is not None
    assert row['Name'] == 'Charlie'

def test_mark_sent(sample_csv):
    handler = DataHandler(sample_csv)
    handler.load_data()
    
    handler.mark_sent(1, "2026-04-03 10:00:00")
    
    assert handler.df.at[1, 'Status'] == 'Sent'
    assert handler.df.at[1, 'Date_Sent'] == "2026-04-03 10:00:00"
    
    df_reloaded = pd.read_csv(sample_csv)
    assert df_reloaded.at[1, 'Status'] == 'Sent'
