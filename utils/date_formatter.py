from datetime import datetime, timedelta

def formatar_data(data_value):
    """
    Formats a date value from Monday.com for display
    
    Args:
        data_value: Date value from Monday.com (could be a list, string or None)
        
    Returns:
        str: Formatted date string in DD/MM/YYYY format, or empty string if invalid
    """
    if isinstance(data_value, list):
        if data_value:
            data_str = data_value[0]  # Get the first element of the list
        else:
            return ''  # Return empty string if list is empty
    elif isinstance(data_value, str):
        data_str = data_value
    else:
        return ''  # Return empty string if not list or string
    
    if data_str:
        try:
            data = datetime.strptime(data_str, '%Y-%m-%d')
            return data.strftime('%d/%m/%Y')
        except ValueError:
            return ''  # Return empty string if date format is incorrect
    return ''

def convert_date_to_monday_format(date_str):
    """
    Converts a date string from DD/MM/YYYY format to YYYY-MM-DD format for Monday.com API
    
    Args:
        date_str (str): Date string in DD/MM/YYYY format
        
    Returns:
        str: Date string in YYYY-MM-DD format, or None if invalid
    """
    try:
        if date_str and date_str != "None":
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            return date_obj.strftime("%Y-%m-%d")
        return None
    except (ValueError, TypeError):
        return None

def subtract_one_day(date_value):
    """
    Subtracts one day from a date value from Monday.com
    
    Args:
        date_value: Date value from Monday.com (could be a list, string or None)
        
    Returns:
        str: Date string in YYYY-MM-DD format for Monday.com API, or None if invalid
    """
    if isinstance(date_value, list):
        if date_value:
            date_str = date_value[0]  # Get the first element of the list
        else:
            return None  # Return None if list is empty
    elif isinstance(date_value, str):
        date_str = date_value
    else:
        return None  # Return None if not list or string
    
    if date_str:
        try:
            # Parse the date string in the format it's returned from Monday.com
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # Subtract one day
            new_date = date_obj - timedelta(days=1)
            # Return in the format needed for Monday.com API
            return new_date.strftime('%Y-%m-%d')
        except ValueError:
            return None  # Return None if date format is incorrect
    return None
